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
    newModel['is_collection'] = oldModel['is_collection']
    $('#item_name').val(oldModel['name'] || '')
    $('#thumbnail_origin').val(oldModel['copied_image_from'] || '').trigger('input')
    $('#item_is_collection').prop('checked', oldModel['is_collection']);
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

async function handleError(response) {
    // Throw error with extended description
    let errorData = {};
    try {
        errorData = await response.json();
    } catch (e) {
        // If response is not JSON, use status text or a default message
        errorData = {message: response.statusText || 'Unknown error'};
    }
    throw new Error(`HTTP ${response.status}: ${errorData.message || response.statusText || 'Unknown error'}`);
}

async function copyImageFromGivenItem(parentUUID, childUUID, alertsElementId) {
    // Make parent use thumbnail from given item
    if (!isUUID(childUUID)) {
        makeAlert(`Incorrect UUID: ${childUUID}`, alertsElementId);
        return;
    }

    if (!isUUID(parentUUID)) {
        makeAlert(`Incorrect UUID: ${parentUUID}`, alertsElementId);
        return;
    }

    if (parentUUID === childUUID) {
        console.log(`Skipping copy thumbnail for ${childUUID} ` +
            `because it points on itself`);
        return;
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 seconds

        const response = await fetch(`${ACTIONS_ENDPOINT}/copy_image/${childUUID}/to/${parentUUID}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            await handleError(response)
        }

        const result = await response.json();
        console.log('Enqueued image copying', result);
        makeAnnounce('Enqueued image copying', alertsElementId);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timed out');
        } else {
            console.error('Failed to enqueue image copying:', error);
            // Handle error appropriately
            describeFail({message: error.message}, alertsElementId);
        }
    }
}

async function saveName(alertsElementId) {
    // Save item name
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 seconds

        const response = await fetch(`${ITEMS_ENDPOINT}/${newModel['uuid']}/name`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'name': newModel['name'],
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            await handleError(response)
        }

        const result = await response.json();
        console.log('Saved item name', result);
        oldModel['name'] = newModel['name'];
        makeAnnounce('New item name saved', alertsElementId);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timed out');
        } else {
            console.error('Failed to save item name:', error);
            describeFail({message: error.message}, alertsElementId);
        }
    }
}

async function saveBasicStuff(alertsElementId) {
    // Save changes
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 seconds

        const response = await fetch(`${ITEMS_ENDPOINT}/${newModel['uuid']}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'is_collection': newModel['is_collection'],
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            await handleError(response)
        }

        const result = await response.json();
        console.log('Saved basic fields', result);
        oldModel['is_collection'] = newModel['is_collection'];
        tryLoadingThumbnail(oldModel['uuid'], $('#thumbnail'));
        makeAnnounce('Basic fields saved', alertsElementId);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timed out');
        } else {
            console.error('Failed to save basic fields:', error);
            describeFail({message: error.message}, alertsElementId);
        }
    }
}

async function saveParent(totalChildren, alertsElementId) {
    // Save new parent
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New parent will affect ${totalChildren} items, are you sure?`)) {
            return;
        }
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 seconds

        const response = await fetch(`${ITEMS_ENDPOINT}/${newModel['uuid']}/parent/${newModel['parent_uuid']}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            await handleError(response)
        }

        const result = await response.json();
        console.log('Saved parent', result);
        oldModel['parent_uuid'] = newModel['parent_uuid'];
        tryLoadingThumbnail(oldModel['parent_uuid'], $('#thumbnail_parent'));
        makeAnnounce('Parent changed', alertsElementId);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timed out');
        } else {
            console.error('Failed to save parent:', error);
            describeFail({message: error.message}, alertsElementId);
        }
    }
}

async function saveTags(totalChildren, alertsElementId) {
    // Save tags
    if (totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New tags will affect ${totalChildren} items, are you sure?`)) {
            return;
        }
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 seconds

        const response = await fetch(`${ITEMS_ENDPOINT}/${newModel['uuid']}/tags`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'tags': newModel['tags'],
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            await handleError(response)
        }

        const result = await response.json();
        console.log('Saved tags', result);
        oldModel['tags'] = newModel['tags'];
        makeAnnounce('Tags saved', alertsElementId);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timed out');
        } else {
            console.error('Failed to save tags:', error);
            describeFail({message: error.message}, alertsElementId);
        }
    }
}

async function savePermissions(totalChildren, alertsElementId) {
    // Save new permissions
    const applyToParents = document.getElementById('item_perm_apply_to_parents').checked;
    const applyToChildren = document.getElementById('item_perm_apply_to_children').checked;
    const applyToChildrenAs = document.getElementById('apply_to_children_as').value;

    if (applyToChildren && totalChildren !== '0' && totalChildren !== '1') {
        if (!confirm(`New permissions will affect ${totalChildren} items, are you sure?`)) {
            return;
        }
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 seconds

        const response = await fetch(`${ITEMS_ENDPOINT}/${newModel['uuid']}/permissions`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'apply_to_parents': applyToParents,
                'apply_to_children': applyToChildren,
                'apply_to_children_as': applyToChildrenAs,
                'permissions': newModel['permissions'],
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            await handleError(response)
        }

        const result = await response.json();
        console.log('Saved permissions', result);
        oldModel['permissions'] = newModel['permissions'];
        initialPermissions = newModel['permissions'];
        makeAnnounce('Permissions saved', alertsElementId);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timed out');
        } else {
            console.error('Failed to save permissions:', error);
            describeFail({message: error.message}, alertsElementId);
        }
    }
}
