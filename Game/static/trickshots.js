// load all trickshots from the server and list them in trickshot-list
var listTricksDoc = document.getElementById("trickshot-list")
var listTricks = []

function list_trickshots() {
    fetch("/trickshots/list")
        .then((r) => r.json())
        .then((r) => {
            listTricks = r;
            const table = document.createElement("table");
            var header = table.insertRow();
            header.innerHTML = "<th>Name</th><th>Difficulty</th>"

            for (let trick of r) {
                var row = table.insertRow();

                var name = trick.name;
                var difficulty = trick.difficulty;
                var id = trick.id;

                row.addEventListener("click", () => {
                    // actually load a trickshot
                    fetch("/trickshots/load", {
                            method: "post",
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({"id": id})
                        }); // there is no answer to be processed :)
                    console.log(id, " clicked")
                    
                })
                row.classList.add("trickshot-table-row");

                var nameCell = row.insertCell();
                var difCell = row.insertCell();

                nameCell.innerText = name;
                difCell.innerText = difficulty + "/10";
            }

            listTricksDoc.innerHTML = "";
            listTricksDoc.appendChild(table);

        })
}

list_trickshots()