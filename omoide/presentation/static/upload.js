const FILES = {}


function addFiles(source) {
    // react on file upload
    let button = $('#upload_media_button')
    button.addClass('upload-in-progress')

    let parent_uuid = $('#parent_uuid').val() || null
    let tags = splitLines($('#item_tags').val())
    let container = $('#media')

    for (let [index, file] of Object.entries(source.files)) {
        if (file.name in FILES)
            continue

        let proxy = createFileProxy(index, file, tags)
        FILES[file.name] = proxy

        let reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = function () {
            proxy.ready = true
            proxy.content = reader.result
            proxy.contentGenerated = true
            proxy.tags = tags
            proxy.parent_uuid = parent_uuid
            proxy.element.appendTo(container)
            proxy.render()

            if (readyToUpload())
                button.removeClass('upload-in-progress')
        }

        reader.onerror = function () {
            makeAlert(reader.error)
        };
    }

    if (readyToUpload())
        button.removeClass('upload-in-progress')
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
        ready: false,
        parentUuid: null,
        isValid: null,
        uuid: null,
        index: Number.parseInt(index),
        size: file.size,
        type: file.type,
        filename: file.name,
        contentExt: extractExt(file.name),
        previewExt: null,
        thumbnailExt: null,
        updatedAt: file.lastModified,
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
            $('<p>', {text: this.filename + ' ' + this.getProgress()}).appendTo(this.element)
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
    if (proxy.filename.length > 255) {
        proxy.status = 'fail'
        proxy.isValid = false
        makeAlert(`Filename is too long: ${proxy.filename}`)
    }

    if (!proxy.contentExt) {
        proxy.status = 'fail'
        proxy.isValid = false
        makeAlert(`File must have an extension: ${proxy.filename}`)
    }

    // TODO - add more extensions
    const valid_extensions = ['jpg']
    if (!valid_extensions.includes(proxy.contentExt)) {
        proxy.status = 'fail'
        proxy.isValid = false
        makeAlert(`File extension must be one of: ${valid_extensions}`)
    }

    proxy.isValid = true
    proxy.steps += 1
    proxy.render()
}

function createItemForProxy(proxy) {
    // send raw data to server and get uuid back
    $.ajax({
        type: 'POST',
        url: '/api/items',
        contentType: 'application/json',
        data: JSON.stringify({
            parent_uuid: proxy.parentUuid,
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
        },
        complete: function () {
            proxy.render()
        },
    })
}

function calcImageSize(width, height, maximum) {
    // calculate new image size
    // FIXME
    let newWidth, newHeight, delta

    if (width > height) {
        newWidth = Math.min(width, maximum)
        delta = width / newWidth
        newHeight = height * delta
    } else {
        newHeight = Math.min(height, maximum)
        delta = height / newHeight
        newWidth = width * delta
    }

    return {
        width: newWidth,
        height: newHeight,
    }
}

function resizeImage(data, maxSize, callback) {
    // resize given image
    const originalImage = new Image();
    originalImage.src = data

    //get a reference to the canvas
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d');

    //wait for the image to load
    originalImage.addEventListener('load', function () {
        let newSize = calcImageSize(
            originalImage.naturalWidth,
            originalImage.naturalHeight,
            maxSize,
        )

        canvas.width = newSize.width;
        canvas.height = newSize.height;

        ctx.drawImage(originalImage, 0, 0, newSize.width, newSize.height);
        callback(canvas.toDataURL('image/jpeg', 0.85))
    });
}

function generatePreviewForProxy(proxy) {
    // generate preview for proxy
    proxy.ready = false

    resizeImage(
        proxy.content,
        1024,
        function (data) {
            proxy.ready = true
            proxy.preview = data
            proxy.previewGenerated = true
            proxy.previewExt = 'jpg'
            proxy.steps += 1
            proxy.render()
        })
}

function generateThumbnailForProxy(proxy) {
    // generate thumbnail for proxy
    proxy.ready = false

    resizeImage(
        proxy.content,
        384,
        function (data) {
            proxy.ready = true
            proxy.thumbnail = data
            proxy.thumbnailGenerated = true
            proxy.thumbnailExt = 'jpg'
            proxy.steps += 1
            proxy.render()
        })
}

function uploadMetaForProxy(proxy) {
    // upload metainfo
    // TODO - add metainfo upload
    proxy.metaUploaded = true
    proxy.steps += 1
}

function saveContentForProxy(proxy) {
    // save content of the proxy on the server
    if (!proxy.content || proxy.contentUploaded)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'content',
            content: proxy.content,
            ext: proxy.contentExt,
        }),
        success: function (response) {
            proxy.contentUploaded = true
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        },
        complete: function () {
            proxy.render()
        },
    })
}

function savePreviewForProxy(proxy) {
    // save preview of the proxy on the server
    if (!proxy.preview || proxy.previewUploaded)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'preview',
            content: proxy.preview,
            ext: proxy.previewExt,
        }),
        success: function (response) {
            proxy.previewUploaded = true
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        },
        complete: function () {
            proxy.render()
        },
    })
}

function saveThumbnailForProxy(proxy) {
    // save thumbnail of the proxy on the server
    if (!proxy.thumbnail || proxy.thumbnailUploaded)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'thumbnail',
            content: proxy.thumbnail,
            ext: proxy.thumbnailExt,
        }),
        success: function (response) {
            proxy.thumbnailUploaded = true
            proxy.steps += 1
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            describeFail(XMLHttpRequest.responseJSON)
            proxy.status = 'fail'
        },
        complete: function () {
            proxy.render()
        },
    })
}

function readyToUpload() {
    // return true if we can actually upload content
    for (let each of Object.values(FILES))
        if (!each.ready) {
            return false
        }
    return true
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
    doIf(targets, generatePreviewForProxy, p => !p.previewGenerated && p.uuid)
    doIf(targets, generateThumbnailForProxy, p => !p.thumbnailGenerated && p.uuid)
    doIf(targets, saveContentForProxy, p => !p.contentUploaded && p.uuid)
    doIf(targets, savePreviewForProxy, p => !p.previewUploaded && p.uuid)
    doIf(targets, saveThumbnailForProxy, p => !p.thumbnailUploaded && p.uuid)
    $(button).removeClass('button-disabled')
}
