const inputBox = document.getElementById("input-box");
const listContainer = document.getElementById("list-container");

// Load tasks from SQLite database when the page loads
document.addEventListener("DOMContentLoaded", fetchTasks);

async function fetchTasks() {
    const response = await fetch('/tasks');
    const tasks = await response.json();
    listContainer.innerHTML = ''; 
    tasks.forEach(task => renderTask(task));
}

function renderTask(task) {
    let li = document.createElement("li");
    li.innerHTML = task.content;
    li.dataset.id = task.id; // Hide the database ID in the HTML element
    
    if (task.completed) {
        li.classList.add("checked");
    }
    
    let span = document.createElement("span");
    span.innerHTML = "\u00d7";
    li.appendChild(span);
    
    listContainer.appendChild(li);
}

async function addTask() {
    if (inputBox.value === '') {
        alert("You must write something!");
        return;
    } 
    
    const taskContent = inputBox.value;
    inputBox.value = "";

    // Send POST request to Flask backend
    const response = await fetch('/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: taskContent })
    });

    if (response.ok) {
        const newTask = await response.json();
        renderTask(newTask); // Show it on the screen immediately
    }
}

inputBox.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        addTask();
    }
});

listContainer.addEventListener("click", async function(e) {
    if (e.target.tagName === "LI") {
        const taskId = e.target.dataset.id;
        
        // Toggle the visual state immediately for a smooth user experience
        e.target.classList.toggle("checked");
        
        // Update database asynchronously
        await fetch(`/toggle/${taskId}`, { method: 'PUT' });
        
    } else if (e.target.tagName === "SPAN") {
        const li = e.target.parentElement;
        const taskId = li.dataset.id;
        
        // Remove from the visual list immediately
        li.remove();
        
        // Delete from database asynchronously
        await fetch(`/delete/${taskId}`, { method: 'DELETE' });
    }
}, false);