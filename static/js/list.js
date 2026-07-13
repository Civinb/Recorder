// 状态变量
let od = true;
let timer;
let astext = "";

// DOM 引用
const input = document.getElementById("search")

// 通用工具
function debounce(fn, ms) {                                        //防抖函数，fn为延迟执行的函数，ms为延迟时间
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

//分页
let pagerows = [];
let currentPage = 1;
let pageSize = 10;
function pageAction(){                                                              //控制页面条目显示
    pagerows.forEach(row =>{
        row.style.display = "none";
    })
    const current = pagerows.slice((currentPage-1)*pageSize, currentPage*pageSize);
    current.forEach(row2=>{
        row2.style.display = "";
    })
}

//向后或向前翻页
function addpage(){                                             
    if(currentPage != Math.ceil(pagerows.length/pageSize)){
        currentPage++;
    }
    pageAction(); 
}

function prepage(){
    if(currentPage != 1){
        currentPage--;
    }
    pageAction();
}

const pre_bt = document.getElementById("pre_bt");
const next_bt = document.getElementById("next_bt");
const size10 = document.getElementById("10");
const size25 = document.getElementById("25");
const size50 = document.getElementById("50");
pre_bt.addEventListener("click", prepage);
next_bt.addEventListener("click", addpage);
size10.addEventListener("click", function(e){
    e.preventDefault();
    changePageSize(10);
})

size25.addEventListener("click", function(e){
    e.preventDefault();
    changePageSize(25);
})

size50.addEventListener("click", function(e){
    e.preventDefault();
    changePageSize(50);
})


function changePageSize(size){
    pageSize = size;
    pageAction();
}


function parseDate(s){
    if (!s) return od ? Infinity : -Infinity;
    const [m, d, y] = s.split('-').map(Number);
    return new Date(y, m - 1, d).getTime();
}


function sortTable(index){
    const tbody = document.querySelector("#table tbody");
    pagerows.sort((a,b) => {
        let x = a.cells[index].innerText.trim();
        let y = b.cells[index].innerText.trim();
        if (index === 1){                                   
            const dx = parseDate(x);
            const dy = parseDate(y);
            return od ? dx - dy : dy - dx;
        }
        return od ? x.localeCompare(y) : y.localeCompare(x);
    })
    od = !od;
    pagerows.forEach(row => tbody.appendChild(row));        
    currentPage = 1;
    pageAction();
}

// 筛选引擎：搜索词 + 类型，两个条件都满足才显示
function filterRows(){
    const rows = document.querySelectorAll("#table tbody tr");
    const aimtype = document.getElementById('typeSelect').value;
    const aimstatus = document.getElementById('statusSelect').value;
    const aimyear = document.getElementById('yearSelect').value;
    let displayedrow = [];
    rows.forEach(row =>{
        const name = row.cells[0].innerText.toLowerCase();
        const date = row.cells[1].innerText;          // 格式 MM-DD-YYYY，可能为空
        const type = row.cells[2].innerText;
        const status = row.cells[3].innerText;

        const year = date ? date.split('-')[2] : "";  

        const matchSearch = name.includes(astext.toLowerCase());
        const matchType = type === aimtype || aimtype === "";
        const matchStatus = status === aimstatus || aimstatus === "";
        const matchYears = year === aimyear || aimyear === "";
        if (matchSearch && matchType && matchStatus && matchYears){
            displayedrow.push(row);
        }
    })
    rows.forEach(row =>{
        row.style.display = "none";
    })
    pagerows = displayedrow;
    currentPage = 1;
    pageAction();
}

// 搜索：更新搜索词后统一筛选
function search(text){
    astext = text;
    filterRows();
}

// 筛选接收
function applyFilter(event) {
    event.preventDefault();
    filterRows();
    document.getElementById('filterTable').close();
}

// 事件接线
const debounced = debounce(search, 300);

input.addEventListener("input", e =>{
    const value = e.target.value.trim();
    debounced(value);
})

filterRows();
