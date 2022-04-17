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

async function createItem(endpoint) {
    // send command for item creation
    let tags = splitLines(document.getElementById('item_tags').value)
    let permissions = splitLines(document.getElementById('item_permissions').value)

    let data = {
        parent_uuid: document.getElementById('parent_uuid').value,
        item_name: document.getElementById('item_name').value,
        is_collection: document.getElementById('item_type_collection').checked,
        tags: tags,
        permissions: permissions
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.status === 201) {
            window.location.href = response.headers.get('location')
        } else {
            const result = await response.json()
            makeAlert(result['detail'])
        }
    } catch (err) {
        throw err
    }
}
