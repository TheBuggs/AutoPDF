const addr = "127.0.0.1";
const port = "5004";

(function () {
  if (checkCookie("user_anonymous_token")) {
    getMyTasks(getCookie("user_anonymous_token"));
  } else {
    setCookie("user_anonymous_token", makeid(64), 60);
  }

  getMyTasks();
})();

function encodeName(str) {
  return encodeURIComponent(str);
}

function makeid(length) {
  var result = "";
  var characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  var charactersLength = characters.length;
  for (var i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

async function uploadFile() {
  let formData = new FormData();
  const user_id = getCookie("user_anonymous_token");

  let appFile = fileupload.files[0];
  let appFilename = appFile.name.replace(/ /g, "_");
  appFilename = encodeName(appFilename);
  var newFile = new File([appFile], encodeName(appFilename), {
    type: appFile.type,
  });

  formData.append("file", newFile);
  formData.append("user", user_id);
  formData.append("fname", appFile.name);

  await fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => getStatus(data.task_id, data.file_id));
}

function removeTableRow(id) {
  row = document.getElementById(id);
  row.parentNode.removeChild(row);
}

async function deleteFile(task_id) {
  const user_id = getCookie("user_anonymous_token");

  fetch(`/delete/${task_id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((res) => removeTableRow(res.task));
}

function handleModal(task) {
  fetch(`/detail/${task}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((res) => openModal(res));
}

function openModal(data) {
  let html = `
  <table>
      <tr>
        <td>ID:</td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td><span>${data["task"][0]}</span><td>
      </tr>
      <tr>
        <td>Дата:</td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td><span>${data["task"][1]}</span><td>
      </tr>
      <tr>
        <td>Файл:</td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td><span>${data["task"][2]}</span><td>
      </tr>
      <tr>
        <td>Заявка:</td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td><span>${data["task"][3]}</span><td>
      </tr>
      <tr>
        <td>Потребител:</td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td><span>${data["task"][4].slice(0, 30) + " . . ."}</span><td>
      </tr>
      <tr>
        <td>Активен:</td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td><span>${data["task"][5]}</span><td>
      </tr>
  </table>`;

  document.getElementById("modal-table").innerHTML = html;
  document.getElementById("backdrop").style.display = "block";
  document.getElementById("exampleModal").style.display = "block";
  document.getElementById("exampleModal").classList.add("show");
}

function closeModal() {
  document.getElementById("backdrop").style.display = "none";
  document.getElementById("exampleModal").style.display = "none";
  document.getElementById("exampleModal").classList.remove("show");
}

var modal = document.getElementById("exampleModal");

window.onclick = function (event) {
  if (event.target == modal) {
    closeModal();
  }
};

function handleClick(type) {
  fetch("/tasks", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ type: type }),
  })
    .then((response) => response.json())
    .then((data) => getStatus(data.task_id, data.file_id));
}

async function getStatus(taskID, fileID) {
  await fetch(`/tasks/${taskID}/${fileID}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((res) => {
      if (res.error === "miss_task") {
        deleteFile(task_id);
        return false;
      }

      if (res.error === "miss_data") {
        return false;
      }

      let disable = " disabled";
      let result_pages = "";

      if (res.task_result) {
        disable = "";

        if (
          typeof res.task_result === "object" ||
          res.task_result instanceof Array
        )
          if ("pages" in res.task_result) {
            result_pages = res.task_result["pages"];
          }
      }

      let timeinfo = `преди ${res.task_created} минути`;
      if (res.task_created == "0") {
        timeinfo = "сега";
      }

      let html = `
      <tr>
        <td>${timeinfo}</td>
        <td><a onclick='handleModal("${taskID}")' href="#"">${res.task_real_name}</a></td>
        <td>${res.task_status}</td>
        <td style="text-align: right"><a href="#" onclick='deleteFile("${taskID}")' class="btn btn-danger btn-sm${disable}" role="button">Изтрии</a></td>
        <td style="text-align: right"><a href="http://${addr}:${port}/download/${fileID}" class="btn btn-primary btn-sm${disable}" role="button">Свали</a></td>
      </tr>`;

      let row = document.getElementById(taskID);
      if (row == null) {
        const table = document.getElementById("tasks");
        row = table.insertRow(0);
        row.setAttribute("id", taskID, 0);
      }

      row.innerHTML = html;

      const taskState = res.task_state;
      if (taskState === "SUCCESS" || taskState === "FAILURE") {
        return false;
      }

      setTimeout(function () {
        getStatus(res.task_id, fileID);
      }, 1000);
    })
    .catch((err) => console.log(err));
}

async function getMyTasks(token) {
  await fetch(`/my/${token}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((res) => {
      res.ids.forEach((item) => {
        getStatus(item[0], item[1]);
      });
    });
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
  let expires = "expires=" + d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  let name = cname + "=";
  let ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function checkCookie(cname) {
  if (getCookie(cname)) {
    return true;
  }

  return false;
}

document
  .querySelector(".custom-file-input")
  .addEventListener("change", function (e) {
    var fileName = document.getElementById("fileupload").files[0].name;
    var nextSibling = e.target.nextElementSibling;
    nextSibling.innerText = fileName;
  });
