const FILES = {}


function arrayBufferToBase64(buffer) {
    let binary = '';
    let bytes = new Uint8Array(buffer);
    let len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}


function base64ToArrayBuffer(base64) {
    let binary_string = window.atob(base64);
    let len = binary_string.length;
    let bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}


function addFiles(source) {
    // react on file upload
    let parent_uuid = $('#parent_uuid').val() || null
    let tags = splitLines($('#item_tags').val())
    let container = $('#media')

    for (let [index, file] of Object.entries(source.files)) {
        if (file.name in FILES)
            continue

        let proxy = createFileProxy(index, file, tags)
        FILES[file.name] = proxy

        let reader = new FileReader();
        reader.readAsArrayBuffer(file);

        reader.onload = function () {
            proxy.file = reader.result
            proxy.tags = tags
            proxy.parent_uuid = parent_uuid
            proxy.element.appendTo(container)
            proxy.render()
        };

        reader.onerror = function () {
            makeAlert(reader.error)
        };
    }
}


function extractExt(filename) {
    // extract extension
    let ext = filename.substring(filename.lastIndexOf('.') + 1, filename.length)
    if (!ext)
        return null
    return ext.toLowerCase()
}

function createFileProxy(index, file, tags) {
    // create new proxy that stores file upload progress
    return {
        parent_uuid: null,
        isValid: null,
        uuid: null,
        index: Number.parseInt(index),
        size: file.size,
        type: file.type,
        filename: file.name,
        ext: extractExt(file.name),
        updated_at: file.lastModified,
        file: null,
        content: null,
        preview: null,
        thumbnail: null,
        metaUploaded: false,
        contentGenerated: false,
        previewGenerated: false,
        thumbnailGenerated: false,
        contentUploaded: false,
        previewUploaded: false,
        thumbnailUploaded: false,
        element: $('<div>', {class: 'upload-element'}),
        features: [],
        status: 'init',
        description: '',
        steps: 0,
        totalSteps: 9,
        tags: tags,
        permissions: [], // TODO - add permissions
        getProgress: function () {
            return (this.steps / this.totalSteps) * 100
        },
        render: function () {
            this.element.empty()
            $('<p>', {text: this.filename}).appendTo(this.element)
        },
    }
}

function doIf(targets, handler, condition) {
    // conditionally iterate on every element
    for (let target of targets) {
        if (target.status !== 'fail' && condition(target))
            handler(target)
    }
}

function validateProxy(proxy) {
    // ensure that content is adequate
    if (!proxy.ext) {
        proxy.status = 'fail'
        proxy.isValid = false
        makeAlert(`File must have an extension: ${proxy.filename}`)
    }

    // TODO - add more extensions
    const valid_extensions = ['jpg']
    if (!valid_extensions.includes(proxy.ext)) {
        proxy.status = 'fail'
        proxy.isValid = false
        makeAlert(`File extension must be one of: ${valid_extensions}`)
    }

    proxy.isValid = true
    proxy.steps += 1
}

function createItemForProxy(proxy) {
    // send raw data to server and get uuid back
    $.ajax({
        type: 'POST',
        url: '/api/items',
        contentType: 'application/json',
        data: JSON.stringify({
            parent_uuid: proxy.parent_uuid,
            name: '',
            is_collection: false,
            tags: proxy.tags,
            permissions: proxy.permissions,
        }),
        success: function (response) {
            proxy.uuid = response['uuid']
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        }
    })
}

function generateContentForProxy(proxy) {
    // generate content for proxy
    proxy.content = arrayBufferToBase64(proxy.file)
    proxy.contentGenerated = true
    proxy.steps += 1
}

function generatePreviewForProxy(proxy) {
    // generate preview for proxy
    // TODO - generate preview
    console.log('generatePreviewForProxy', proxy)
    proxy.previewGenerated = true
    proxy.steps += 1
}

function generateThumbnailForProxy(proxy) {
    // generate thumbnail for proxy
    // TODO - generate thumbnail
    console.log('generateThumbnailForProxy', proxy)
    proxy.thumbnailGenerated = true
    proxy.steps += 1
}

function uploadMetaForProxy(proxy) {
    // upload metainfo
    // TODO - add metainfo upload
    proxy.metaUploaded = true
    proxy.steps += 1
}

function saveContentForProxy(proxy) {
    // save content of the proxy on the server
    if (!proxy.content)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'content',
            content: proxy.content,
        }),
        success: function (response) {
            proxy.contentSent = true
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        }
    })
}

function savePreviewForProxy(proxy) {
    // save preview of the proxy on the server
    if (!proxy.preview)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'preview',
            content: proxy.preview,
        }),
        success: function (response) {
            proxy.previewSent = true
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        }
    })
}

function saveThumbnailForProxy(proxy) {
    // save thumbnail of the proxy on the server
    if (!proxy.thumbnail)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'thumbnail',
            content: proxy.thumbnail,
        }),
        success: function (response) {
            proxy.thumbnailSent = true
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        }
    })
}

function uploadMedia(button) {
    // upload given media to the backend
    let targets

    if ($('#upload_as').val() === 'children')
        targets = Object.values(FILES)
    else
        targets = Object.values(FILES)[0]

    targets.sort((a, b) => a.index > b.index ? 1 : -1)

    $(button).addClass('button-disabled')
    doIf(targets, validateProxy, p => !p.uuid && p.isValid === null)
    doIf(targets, createItemForProxy, p => !p.uuid)
    doIf(targets, uploadMetaForProxy, p => !p.metaUploaded && p.uuid)
    doIf(targets, generateContentForProxy, p => !p.contentGenerated && p.uuid)
    doIf(targets, generatePreviewForProxy, p => !p.previewGenerated && p.uuid)
    doIf(targets, generateThumbnailForProxy, p => !p.thumbnailGenerated && p.uuid)
    doIf(targets, saveContentForProxy, p => !p.contentUploaded && p.uuid)
    doIf(targets, savePreviewForProxy, p => !p.previewUploaded && p.uuid)
    doIf(targets, saveThumbnailForProxy, p => !p.thumbnailUploaded && p.uuid)
    $(button).removeClass('button-disabled')
}
