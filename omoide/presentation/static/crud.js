function splitLines(text) {
    // split string by line separators and return only non empty
    return text.replace(/\r\n/, '\n').split('\n').filter(n => n)
}

function makeAlert(text) {
    // create popup message
    let target = document.getElementById('alerts')
    let alert = document.createElement('div')

    alert.innerHTML = `
        <div class="alert">
            <span class="closebtn"
                  onclick="this.parentElement.style.display='none';">&times;</span>
            ${text}
        </div>`

    target.appendChild(alert)
}

function gatherItemParameters() {
    // gather information from typical creation fields
    let tags = splitLines(document.getElementById('item_tags').value)
    let permissions = splitLines(document.getElementById('item_permissions').value)
    return {
        parent_uuid: document.getElementById('parent_uuid').value,
        is_collection: document.getElementById('item_type_collection').checked,
        tags: tags,
        permissions: permissions
    }
}

async function createItem(endpoint) {
    // send command for item creation
    let data = gatherItemParameters()
    data['item_name'] = document.getElementById('item_name').value
    await request(endpoint, data)
}

async function uploadItems(endpoint) {
    // send command for item creation
    let data = gatherItemParameters()
    await request(endpoint, data)
}

async function request(endpoint, payload) {
    // made HTTP POST request
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json()
        if (response.status === 201) {
            let url = result.get('url')
            if (url !== undefined)
                window.location.href = url
        } else {
            makeAlert(result['detail'])
        }
    } catch (err) {
        throw err
    }
}
