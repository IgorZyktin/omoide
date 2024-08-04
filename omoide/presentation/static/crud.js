function gatherItemParameters() {
    // gather information for item creation
    let raw_uuid = $('#parent_uuid').val()
    let parent_uuid

    if (isUUID(raw_uuid)) {
        parent_uuid = raw_uuid
    } else {
        parent_uuid = null
    }

    return {
        parent_uuid: parent_uuid,
        is_collection: $('#item_is_collection').is(':checked'),
        name: $('#item_name').val().trim(),
        tags: splitLines($('#item_tags').val()),
        permissions: extractUUIDs($('#item_permissions').val()),
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
    $.ajax({
        type: 'POST',
        url: endpoint,
        contentType: 'application/json',
        data: JSON.stringify(parameters),
        beforeSend: function () {
            $(button).addClass('button-disabled')
        },
        success: function (response) {
            let action = $('#action_after_creation').val()
            let uuid = response['item']['uuid']
            if (action === 'upload') {
                relocateWithAim(`/upload/${uuid}`)
            } else if (action === 'nothing') {
                makeAnnounce(`Created ${uuid}`)
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


async function deleteItem(button, uuid) {
    // send command for item deletion
    $.ajax({
        type: 'DELETE',
        url: `${ITEMS_ENDPOINT}/${uuid}`,
        contentType: 'application/json',
        beforeSend: function () {
            $(button).addClass('button-disabled')
        },
        success: function (response) {
            let uuid = response['parent_uuid']

            if (uuid)
                relocateWithAim(`/browse/${uuid}`)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
        },
        complete: function () {
            $(button).removeClass('button-disabled')
        }
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
                console.log(`Problem: ${problem}`)
                makeAlert(problem.msg)
            }
        }
    } catch (err) {
        throw err
    }
}

function isUUID(uuid) {
    let s = "" + uuid;
    s = s.match(UUID_REGEXP);
    return s !== null;
}

function tryLoadingThumbnail(uuid, thumbnailElement, callback) {
    // try to load thumbnail for the item
    if (!isUUID(uuid)) {
        thumbnailElement.empty()
        renderThumbnailStatic(thumbnailElement, EMPTY_FILE)
        return
    }

    thumbnailElement.empty()

    $.ajax({
        type: 'GET',
        url: `${ITEMS_ENDPOINT}/${uuid}`,
        contentType: 'application/json',
        success: function (response) {
            renderThumbnailDynamic(thumbnailElement, response)

            if (callback !== undefined)
                callback(response)
        },
    })
}
