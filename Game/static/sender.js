/*
    Standard file for interfacing with the server
    Essentially just a wrapper for fetch. This is only for updating the backend, it does not handle responses
*/

function sender(apiEndpoint, jsonData) {
    fetch(apiEndpoint, {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
}