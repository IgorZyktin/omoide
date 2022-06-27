function splitLines(text) {
    // split string by line separators and return only non-empty
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
    let tags = splitLines($('#item_tags').val())
    // TODO - restore after permissions will be introduced
    let permissions = []
    // let permissions = splitLines($('#item_permissions').val())
    return {
        parent_uuid: $('#parent_uuid').val() || null,
        is_collection: $('#treat-item-as').val() === 'collection',
        name: $('#item_name').val(),
        tags: tags,
        permissions: permissions,
    }
}

function describeFail(response) {
    // generate human readable error message
    if (typeof response['detail'] === 'string') {
        console.log('Error: ' + JSON.stringify(response['detail']))
        makeAlert(response['detail'])
    } else {
        for (const problem of response['detail']) {
            console.log('Error: ' + JSON.stringify(problem))
            makeAlert(problem.msg)
        }
    }
}


async function createItem(button, parameters) {
    // send command for item creation
    $.ajax({
        type: 'POST',
        url: '/api/items',
        contentType: 'application/json',
        data: JSON.stringify(parameters),
        beforeSend: function () {
            $(button).addClass('button-disabled')
        },
        success: function (response) {
            let action = $('#action-after-creation').val()
            let uuid = response['object']['uuid']
            if (action === 'upload') {
                relocateWithAim(`/upload`, {'parent_uuid': uuid})
            } else if (action === 'nothing') {
                // do nothing
            } else if (parameters['is_collection']) {
                relocateWithAim(`/browse/${uuid}`)
            } else {
                relocateWithAim(`/preview/${uuid}`)
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
        },
        complete: function () {
            $(button).removeClass('button-disabled')
        }
    })
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
    s = s.match(/^[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}$/g);
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
