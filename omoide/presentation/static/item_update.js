const BASIC_TEXT_FIELDS = [
    'name',
    'content_ext',
    'preview_ext',
    'thumbnail_ext',
]

const BASIC_BOOL_FIELDS = [
    'is_collection',
]

const BASIC_FIELDS = BASIC_TEXT_FIELDS.concat(BASIC_BOOL_FIELDS)


function alterModelTextField(element, fieldName) {
    // change item model field
    newModel[fieldName] = $(element).val().trim()
}


function alterModelBoolField(element, fieldName) {
    // change item model field
    newModel[fieldName] = $(element).is(':checked')
}

function alterModelParentField(element) {
    // change item model field
    let value = $(element).val().trim()
    newModel['parent_uuid'] = value || null
    tryLoadingThumbnail(newModel['parent_uuid'], $('#thumbnail_parent'))
}

function alterModelTagsField(element) {
    // change item model field
    newModel['tags'] = splitLines($(element).val())
}

function alterModelPermissionsField(element) {
    // change item model field
    newModel['permissions'] = extractUUIDs($(element).val())
}

function resetBasic() {
    // restore parameters
    for (let field of BASIC_FIELDS) {
        newModel[field] = oldModel[field]
    }

    $('#item_name').val(oldModel['name'] || '')
    $('#thumbnail_origin').val(oldModel['copied_image_from'] || '').trigger('input')
    $('#item_is_collection').prop('checked', oldModel['is_collection']);
    $('#item_content_ext').val(oldModel['content_ext'] || '')
    $('#item_preview_ext').val(oldModel['preview_ext'] || '')
    $('#item_thumbnail_ext').val(oldModel['thumbnail_ext'] || '')
}

function resetTags() {
    // restore parameters
    newModel['tags'] = oldModel['tags']
    fillTextarea('item_tags', oldModel['tags'])
}

function resetPermissions() {
    // restore parameters
    newModel['permissions'] = oldModel['permissions']
    fillTextarea('item_permissions', initialPermissions)
}

function resetParent() {
    // restore parameters
    newModel['parent_uuid'] = oldModel['parent_uuid']
    $('#item_parent').val(oldModel['parent_uuid'] || '')
    tryLoadingThumbnail(oldModel['parent_uuid'], $('#thumbnail_parent'))
}

function fillTextarea(elementId, values) {
    // fill textarea using array
    let lines = values.join('\n').trim()
    $('#' + elementId).val(lines)
}

function copyImageFromGivenItem(parentUUID, childUUID, alertsElementId) {
    // make parent use thumbnail from given item
    if (!isUUID(childUUID)) {
        makeAlert(`Incorrect UUID: ${childUUID}`, alertsElementId)
        return;
    }

    if (!isUUID(parentUUID)) {
        makeAlert(`Incorrect UUID: ${childUUID}`, alertsElementId)
        return;
    }

    if (parentUUID === childUUID) {
        console.log(`Skipping copy thumbnail for ${childUUID} ` +
            `because it points on itself`)
        return
    }

    $.ajax({
        timeout: 5000, // 5 seconds
        type: 'POST',
        url: `${ACTIONS_ENDPOINT}/copy_image`,
        data: JSON.stringify({
            'source_item_uuid': childUUID,
            'target_item_uuid': parentUUID,
        }),
        contentType: 'application/json',
        success: function (response) {
            console.log('Enqueued image copying', response)
            makeAnnounce('Enqueued image copying', alertsElementId)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON, alertsElementId)
        },
    })
}

function saveBasicStuff(alertsElementId) {
    // save changes
    $.ajax({
        timeout: 5000, // 5 seconds
        type: 'PATCH',
        url: `/api/items/${newModel['uuid']}`,
        contentType: 'application/json',
        data: JSON.stringify([
            {
                'op': 'replace',
                'path': '/name',
                'value': newModel['name'],
            },
            {
                'op': 'replace',
                'path': '/content_ext',
                'value': newModel['content_ext'],
            },
            {
                'op': 'replace',
                'path': '/preview_ext',
                'value': newModel['preview_ext'],
            },
            {
                'op': 'replace',
                'path': '/thumbnail_ext',
                'value': newModel['thumbnail_ext'],
            },
            {
                'op': 'replace',
                'path': '/is_collection',
                'value': newModel['is_collection'],
            },
        ]),
        success: function (response) {
            console.log('Saved basic fields', response)
            for (let field of BASIC_FIELDS) {
                oldModel[field] = newModel[field]
            }
            tryLoadingThumbnail(oldModel['uuid'], $('#thumbnail'))
            makeAnnounce('Basic fields saved', alertsElementId)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON, alertsElementId)
        },
    })
}

function saveParent(totalChildren, alertsElementId) {
    // save changes
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New parent will affect ${totalChildren} items, are you sure?`))
            return
    }
    $.ajax({
        timeout: 5000, // 5 seconds
        type: 'PUT',
        url: `/api/items/${newModel['uuid']}/parent/${newModel['parent_uuid']}`,
        contentType: 'application/json',
        success: function (response) {
            console.log('Saved parent', response)
            oldModel['parent_uuid'] = newModel['parent_uuid']
            tryLoadingThumbnail(oldModel['parent_uuid'], $('#thumbnail_parent'))
            makeAnnounce('Parent changed', alertsElementId)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON, alertsElementId)
        },
    })
}

function saveTags(totalChildren, alertsElementId) {
    // save changes
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New tags will affect ${totalChildren} items, are you sure?`))
            return
    }

    $.ajax({
        timeout: 5000, // 5 seconds
        type: 'PUT',
        url: `/api/items/${newModel['uuid']}/tags`,
        contentType: 'application/json',
        data: JSON.stringify({
            'tags': newModel['tags'],
        }),
        success: function (response) {
            console.log('Saved tags', response)
            oldModel['tags'] = newModel['tags']
            makeAnnounce('Tags saved', alertsElementId)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON, alertsElementId)
        },
    })
}

function savePermissions(totalChildren, alertsElementId) {
    // save changes
    let applyToParents = $('#item_perm_apply_to_parents').is(':checked')
    let applyToChildren = $('#item_perm_apply_to_children').is(':checked')
    let override = $('#propagate_permissions').val() === 'copy'

    if (applyToChildren && totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New permissions will affect ${totalChildren} items, are you sure?`))
            return
    }

    $.ajax({
        timeout: 5000, // 5 seconds
        type: 'PUT',
        url: `/api/items/${newModel['uuid']}/permissions`,
        contentType: 'application/json',
        data: JSON.stringify({
            'apply_to_parents': applyToParents,
            'apply_to_children': applyToChildren,
            'override': override,
            'permissions_before': oldModel['permissions'],
            'permissions_after': newModel['permissions'],
        }),
        success: function (response) {
            console.log('Saved permissions', response)
            oldModel['permissions'] = newModel['permissions']
            initialPermissions = newModel['permissions']
            makeAnnounce('Permissions saved', alertsElementId)
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON, alertsElementId)
        },
    })
}
