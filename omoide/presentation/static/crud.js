function gatherItemParameters(owner_uuid) {
    // gather information for item creation
    const rawUUID = document.getElementById('parent_uuid').value
    const parentUUID = isUUID(rawUUID) ? rawUUID : null

    const permissionsText = document.getElementById('item_permissions').value
    const permissions = []
    for (const match of permissionsText.matchAll(UUID_REGEXP)) {
        permissions.push({uuid: match[0], name: ''})
    }

    return {
        owner_uuid: owner_uuid,
        parent_uuid: parentUUID,
        is_collection: document.getElementById('item_is_collection').checked,
        name: document.getElementById('item_name').value.trim(),
        tags: splitLines(document.getElementById('item_tags').value),
        permissions: permissions,
    }
}

function describeFail(response, alertsElementId) {
    // generate human readable error message
    if (response === undefined) {
        // TODO - make message more adequate
        makeAlert('Something bad happened', alertsElementId)
    } else if (typeof response['detail'] === 'string') {
        console.log('Error: ' + JSON.stringify(response['detail']))
        makeAlert(response['detail'], alertsElementId)
    } else {
        for (const problem of response['detail']) {
            console.log('Error: ' + JSON.stringify(problem))
            makeAlert(problem.msg, alertsElementId)
        }
    }
}


async function createItem(button, endpoint, parameters) {
    // send command for item creation
    button.classList.add('button-disabled')
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(parameters),
        })

        const data = await response.json().catch(() => undefined)

        if (!response.ok) {
            describeFail(data)
            return
        }

        const action = document.getElementById('action_after_creation').value
        const uuid = data['item']['uuid']
        if (action === 'upload') {
            relocateWithAim(`/upload/${uuid}`)
        } else if (action === 'nothing') {
            makeAnnounce(`Created ${uuid}`)
        } else if (parameters['is_collection']) {
            relocateWithAim(`/browse/${uuid}`)
        } else {
            relocateWithAim(`/preview/${uuid}`)
        }
    } catch (err) {
        console.error('Failed to create item:', err)
        describeFail(undefined)
    } finally {
        button.classList.remove('button-disabled')
    }
}


async function deleteItem(button, uuid, relocate = true) {
    // send command for item deletion
    const searchParams = new URLSearchParams(window.location.search)

    button.classList.add('button-disabled')
    try {
        const response = await fetch(`${ITEMS_ENDPOINT}/${uuid}`, {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
        })

        const data = await response.json().catch(() => undefined)

        if (!response.ok) {
            describeFail(data)
            return false
        }

        if (relocate) {
            const switchTo = data['switch_to']
            if (switchTo.is_collection) {
                relocateWithAim(`/browse/${switchTo.uuid}` + '?' + searchParams.toString())
            } else {
                relocateWithAim(`/preview/${switchTo.uuid}` + '?' + searchParams.toString())
            }
        }
        return true
    } catch (err) {
        console.error('Failed to delete item:', err)
        describeFail(undefined)
        return false
    } finally {
        button.classList.remove('button-disabled')
    }
}

async function request(endpoint, payload, callback) {
    // make HTTP POST request
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
    })

    const result = await response.json()
    if (response.status === 200 || response.status === 201) {
        callback(response.headers, result)
    } else {
        for (const problem of result['detail']) {
            console.log(`Problem: ${problem}`)
            makeAlert(problem.msg)
        }
    }
}

function isUUID(uuid) {
    const text = '' + uuid
    return text.match(UUID_REGEXP) !== null
}

async function tryLoadingThumbnail(uuid, thumbnailElement, callback) {
    // try to load thumbnail for the item
    if (!isUUID(uuid)) {
        thumbnailElement.replaceChildren()
        renderThumbnailStatic(thumbnailElement, EMPTY_FILE)
        return
    }

    thumbnailElement.replaceChildren()

    try {
        const response = await fetch(`${ITEMS_ENDPOINT}/${uuid}`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json'},
        })

        if (!response.ok) {
            return
        }

        const data = await response.json()
        if (data['item'] !== undefined) {
            renderThumbnailDynamic(thumbnailElement, data['item'])
        }

        if (callback !== undefined) {
            callback(data)
        }
    } catch (err) {
        console.error(`Failed to load thumbnail for ${uuid}:`, err)
    }
}
