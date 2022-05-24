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
        parent_uuid: document.getElementById('parent_uuid').value || null,
        is_collection: document.getElementById('is_collection').checked,
        name: document.getElementById('item_name').value,
        tags: tags,
        permissions: permissions
    }
}

async function createItem(endpoint) {
    // send command for item creation
    let data = gatherItemParameters()
    data['item_name'] = document.getElementById('item_name').value

    function onCreate(headers, result) {
        let goUpload = document.getElementById('go_upload').checked
        let url = ''

        if (goUpload) {
            url = result['upload_url']
        } else {
            url = result['url']
        }

        if (url !== undefined && url !== '')
            window.location.href = url
    }

    await request(endpoint, data, onCreate)
}


async function deleteItem(endpoint) {
    // send command for item deletion
    try {
        const response = await fetch(endpoint, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json'
            },
        });

        const result = await response.json()
        if (response.status === 200) {
            let url = result['url']

            if (!url)
                return

            window.location.href = url
        } else {
            if (typeof result['detail'] === 'string') {
                console.log(result['detail'])
                makeAlert(result['detail'])
            } else {
                for (const problem of result['detail']) {
                    console.log(problem)
                    makeAlert(problem.msg)
                }
            }
        }
    } catch (err) {
        throw err
    }
}

async function uploadItems(endpoint) {
    // send command for item creation
    let data = gatherItemParameters()
    await request(endpoint, data, () => {
    })
}

async function request(endpoint, payload, callback) {
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
        if (response.status === 200 || response.status === 201) {
            callback(response.headers, result)
        } else {
            for (const problem of result['detail']) {
                console.log(problem)
                makeAlert(problem.msg)
            }
        }
    } catch (err) {
        throw err
    }
}

function isUUID(uuid) {
    let s = "" + uuid;
    s = s.match(/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/g);
    return s !== null;
}

function srcFromUUID(user_uuid, uuid) {
    // generate item thumbnail url from uuid
    let prefix = uuid.slice(0, 2)
    return `/content/${user_uuid}/thumbnail/${prefix}/${uuid}.jpg`
}

function tryLoadingThumbnail(user_uuid, defaultSrc) {
    // try to load thumbnail for item
    let uuid = document.getElementById('parent_uuid')

    if (uuid === undefined)
        return

    let image = document.getElementById('item_thumbnail')

    if (image === undefined)
        return

    if (isUUID(uuid.value)) {
        image.src = srcFromUUID(user_uuid, uuid.value)
    } else {
        image.src = defaultSrc
    }
}
