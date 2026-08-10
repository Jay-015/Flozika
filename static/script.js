const dropZone=document.getElementById("dropZone");
const fileInput=document.getElementById("fileInput");
const error = document.getElementById("error");

// navbar

const menuBtn = document.querySelector(".menu-btn");
const navLinks = document.querySelector(".nav-links");
const icon = menuBtn.querySelector("i");

menuBtn.addEventListener("click", () => {
    navLinks.classList.toggle("active");

    if(navLinks.classList.contains("active")){
        icon.classList.remove("fa-bars");
        icon.classList.add("fa-xmark");
    }else{
        icon.classList.remove("fa-xmark");
        icon.classList.add("fa-bars");
    }
});

// nav end

dropZone.addEventListener("click",()=>fileInput.click());

dropZone.addEventListener("dragover",(e)=>{
e.preventDefault();
dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave",()=>{
dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop",(e)=>{
e.preventDefault();
fileInput.files=e.dataTransfer.files;
showFileInfo(fileInput.files[0]);
dropZone.classList.remove("dragover");
});

fileInput.addEventListener("change",()=>{
showFileInfo(fileInput.files[0]);
});

function showFileInfo(file){
document.getElementById("fileName").innerText="File: "+file.name;
document.getElementById("fileSize").innerText=
"Size: "+(file.size/1024/1024).toFixed(2)+" MB";
}


fileInput.addEventListener("change", function () {

    const file = this.files[0];
    if (!file) return;

    const extension = file.name.split(".").pop().toLowerCase();

    let maxSize;

    switch (extension) {
        case "jpg":
        case "jpeg":
        case "png":
            maxSize = 10 * 1024 * 1024; // 10 MB
            break;

        case "pdf":
            maxSize = 25 * 1024 * 1024; // 25 MB
            break;

        case "doc":
        case "docx":
            maxSize = 20 * 1024 * 1024; // 20 MB
            break;

        default:
            error.textContent = "Unsupported file type.";
            this.value = "";
            return;
    }

    if (file.size > maxSize) {
        error.textContent = `Maximum allowed size for .${extension} files is ${maxSize / (1024 * 1024)} MB.`;
        this.value = "";
    } else {
        error.textContent = "";
    }
});