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

const UUID_REGEXP = /[0-9A-F]{8}-[0-9A-F]{4}-[4][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}/ig

function alterModelTextField(element, fieldName) {
    // change item model field
    newModel[fieldName] = $(element).val().trim()
    checkChangesBasic('save_basic')
}


function alterModelBoolField(element, fieldName) {
    // change item model field
    newModel[fieldName] = $(element).is(':checked')
    checkChangesBasic('save_basic')
}

function alterModelParentField(element, fieldName) {
    // change item model field
    let value = $(element).val().trim()
    newModel[fieldName] = value || null
    checkChangesParent('save_parent')
}

function alterModelTagsField(element) {
    // change item model field
    newModel['tags'] = splitLines($(element).val())
    checkChangesTags('save_tags')
}

function alterModelPermissionsField(element) {
    // change item model field
    newModel['permissions'] = [...$(element).val().matchAll(UUID_REGEXP)].flat()
    checkChangesPermissions('save_permissions')
}

function checkChangesBasic(elementId) {
    // toggle save button for basic fields
    checkChanges(oldModel, newModel, elementId, BASIC_FIELDS, [])
}

function checkChangesParent(elementId) {
    // toggle save button for basic fields
    checkChanges(oldModel, newModel, elementId, ['parent_uuid'], [])
}

function checkChangesTags(elementId) {
    // toggle save button for tags
    checkChanges(oldModel, newModel, elementId, [], ['tags'])
}

function checkChangesPermissions(elementId) {
    // toggle save button for permissions
    checkChanges(oldModel, newModel, elementId, [], ['permissions'])
}

function checkChanges(oldModel, newModel, elementId, fields, arrayFields) {
    // toggle save button for basic fields
    let changed = false
    let button = $('#' + elementId)

    for (let field of fields) {
        if (oldModel[field] !== newModel[field]) {
            changed = true
            break
        }
    }

    if (!changed) {
        for (let field of arrayFields) {
            if (!arraysAreIdentical(oldModel[field], newModel[field])) {
                changed = true
                break
            }
        }
    }

    if (changed) {
        button.removeClass('button-disabled')
        button.prop('disabled', false);
    } else {
        button.addClass('button-disabled')
        button.prop('disabled', true);
    }
}

function resetBasic() {
    // restore parameters
    for (let field of BASIC_FIELDS) {
        newModel[field] = oldModel[field]
    }

    $('#item_name').val(oldModel['name'] || '')
    $('#item_is_collection').prop('checked', oldModel['is_collection']);
    $('#item_content_ext').val(oldModel['content_ext'] || '')
    $('#item_preview_ext').val(oldModel['preview_ext'] || '')
    $('#item_thumbnail_ext').val(oldModel['thumbnail_ext'] || '')
    checkChangesBasic('save_basic')
}

function resetTags() {
    // restore parameters
    newModel['tags'] = oldModel['tags']
    fillTextarea('item_tags', oldModel['tags'])
    checkChangesTags('save_tags')
}

function resetPermissions() {
    // restore parameters
    newModel['permissions'] = oldModel['permissions']
    fillTextarea('item_permissions', initialPermissions)
    checkChangesPermissions('save_permissions')
}

function resetParent() {
    // restore parameters
    newModel['parent_uuid'] = oldModel['parent_uuid']
    $('#item_parent').val(oldModel['parent_uuid'] || '')
    tryLoadingThumbnail(oldModel['parent_uuid'], $('#parent_thumbnail'))
    checkChangesParent('save_parent')
}

function fillTextarea(elementId, values) {
    // fill textarea using array
    let lines = values.join('\n').trim()
    $('#' + elementId).val(lines)
}

function saveBasic() {
    // save changes
    alert('saveBasic')  // FIXME
}

function saveParent(totalChildren) {
    // save changes
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New parent will affect ${totalChildren} items, are you sure?`))
            return
    }
    alert('saveParent')  // FIXME
}

function saveTags(totalChildren) {
    // save changes
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New tags will affect ${totalChildren} items, are you sure?`))
            return
    }
    alert('saveTags') // FIXME
}

function savePermissions(totalChildren) {
    // save changes
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New permissions will affect ${totalChildren} items, are you sure?`))
            return
    }
    let applyToParents = $('#item_perm_apply_to_parents').is(':checked')
    let applyToChildren = $('#item_perm_apply_to_children').is(':checked')
    alert('savePermissions') // FIXME
}
