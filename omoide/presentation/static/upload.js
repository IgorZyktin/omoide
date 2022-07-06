const FILES = {}
const PREVIEW_SIZE = 1024
const THUMBNAIL_SIZE = 384
const ICON_SIZE = 128
const EMPTY_FILE = '/static/empty.png'


function addFiles(source) {
    // react on file upload
    let button = $('#upload_media_button')
    button.addClass('upload-in-progress')

    let parent_uuid = $('#parent_uuid').val() || null
    let tags = splitLines($('#item_tags').val())
    let container = $('#media')

    for (let file of Object.values(source.files)) {
        if (file.name in FILES)
            continue

        let proxy = createFileProxy(file, tags)
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

function createFileProxy(file, tags) {
    // create new proxy that stores file upload progress
    return {
        ready: false,
        parentUuid: null,
        isValid: null,
        uuid: null,
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
        icon: null,
        metaUploaded: false,
        contentGenerated: false,
        previewGenerated: false,
        thumbnailGenerated: false,
        iconGenerated: false,
        contentUploaded: false,
        previewUploaded: false,
        thumbnailUploaded: false,
        element: $('<div>', {class: 'upload-element'}),
        features: [],
        status: 'init',
        description: '',
        steps: 0,
        totalSteps: 9,  // tags are not counted as a step
        tags: tags,
        permissions: [], // TODO - add permissions
        getProgress: function () {
            return (this.steps / this.totalSteps) * 100
        },
        render: function () {
            this.element.empty()
            if (this.icon) {
                $('<img>', {
                    src: this.icon,
                    width: ICON_SIZE,
                    height: 'auto',
                }).appendTo(this.element)
            } else {
                $('<img>', {
                    src: EMPTY_FILE,
                    width: ICON_SIZE,
                    height: 'auto',
                }).appendTo(this.element)
            }
            let lines = $('<div>', {class: 'upload-lines'})

            $('<p>', {
                text: this.filename,
            }).appendTo(lines)

            $('<progress>', {
                value: this.getProgress(),
                max: 100,
            }).appendTo(lines)
            lines.appendTo(this.element)
        },
    }
}

async function doIf(targets, handler, condition) {
    // conditionally iterate on every element
    for (let target of targets) {
        if (target.status !== 'fail' && condition(target)) {
            console.log(`Doing ${handler.name}`)
            await handler(target)
        }
    }
}

async function validateProxy(proxy) {
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

async function createItemForProxy(proxy) {
    // send raw data to server and get uuid back
    return new Promise(function (resolve, reject) {
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
                reject('fail')
            },
            complete: function () {
                proxy.render()
                resolve('ok')
            },
        })
    })
}

function calcImageSize(originalWidth, originalHeight,
                       targetWidth, targetHeight) {
    // calculate new image size
    if (![originalWidth, originalHeight,
        targetWidth, targetHeight].every(element => element)) {
        console.log(`Bad dimensions for image conversion: 
        (w=${originalWidth}, h=${originalHeight})
         => (w=${targetWidth}, h=${targetHeight})`)

        return {
            width: originalWidth,
            height: originalHeight,
        }
    }

    let dimension = Math.min(targetHeight, originalHeight)
    let coefficient = dimension / originalHeight
    return {
        width: Math.ceil(coefficient * originalWidth),
        height: dimension,
    }
}

async function resizeImage(data, targetWidth, targetHeight, callback) {
    // resize given image
    const originalImage = new Image();
    originalImage.src = data

    //get a reference to the canvas
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d');

    return new Promise(function (resolve, reject) {
        //wait for the image to load
        originalImage.addEventListener('load', function () {
            let newSize = calcImageSize(
                originalImage.naturalWidth,
                originalImage.naturalHeight,
                targetWidth,
                targetHeight,
            )

            canvas.width = newSize.width;
            canvas.height = newSize.height;

            ctx.drawImage(originalImage, 0, 0, newSize.width, newSize.height);
            callback(canvas.toDataURL('image/jpeg', 0.85))
            resolve('ok')
        });
    })
}

async function generatePreviewForProxy(proxy) {
    // generate preview for proxy
    proxy.ready = false
    await resizeImage(
        proxy.content,
        PREVIEW_SIZE,
        PREVIEW_SIZE,
        function (data) {
            proxy.ready = true
            proxy.preview = data
            proxy.previewGenerated = true
            proxy.previewExt = 'jpg'
            proxy.steps += 1
            proxy.render()
        })
}

async function generateThumbnailForProxy(proxy) {
    // generate thumbnail for proxy
    proxy.ready = false
    await resizeImage(
        proxy.content,
        THUMBNAIL_SIZE,
        THUMBNAIL_SIZE,
        function (data) {
            proxy.ready = true
            proxy.thumbnail = data
            proxy.thumbnailGenerated = true
            proxy.thumbnailExt = 'jpg'
            proxy.steps += 1
            proxy.render()
        })
}

async function generateIconForProxy(proxy) {
    // generate tiny thumbnail for proxy
    proxy.ready = false
    await resizeImage(
        proxy.content,
        ICON_SIZE,
        ICON_SIZE,
        function (data) {
            proxy.ready = true
            proxy.icon = data
            proxy.iconGenerated = true
            proxy.steps += 1
            proxy.render()
        })
}

async function uploadMetaForProxy(proxy) {
    // upload metainfo
    // TODO - add metainfo upload
    proxy.metaUploaded = true
    proxy.steps += 1
}

async function uploadTagsProxy(proxy) {
    // upload tags
    // TODO - add tags upload
}

async function saveContentForProxy(proxy) {
    // save content of the proxy on the server
    if (!proxy.content || proxy.contentUploaded)
        return

    $.ajax({
        type: 'PUT',
        url: `/api/media/${proxy.uuid}`,
        contentType: 'application/json',
        data: JSON.stringify({
            type: 'content',
            origin: 'direct',
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

async function savePreviewForProxy(proxy) {
    // save preview of the proxy on the server
    if (!proxy.preview || proxy.previewUploaded)
        return

    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'PUT',
            url: `/api/media/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                type: 'preview',
                origin: 'direct',
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
                reject('fail')
            },
            complete: function () {
                proxy.render()
                resolve('ok')
            },
        })
    })
}

async function saveThumbnailForProxy(proxy) {
    // save thumbnail of the proxy on the server
    if (!proxy.thumbnail || proxy.thumbnailUploaded)
        return

    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'PUT',
            url: `/api/media/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                type: 'thumbnail',
                origin: 'direct',
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
                reject('fail')
            },
            complete: function () {
                proxy.render()
                resolve('ok')
            },
        })
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

function getTargets() {
    // get upload targets in correct order
    let targets

    if ($('#upload_as').val() === 'children')
        targets = Object.values(FILES)
    else
        targets = Object.values(FILES)[0]

    targets.sort((a, b) => a.filename > b.filename ? 1 : -1)

    return targets
}

async function preprocessMedia(button) {
    // prepare given media for upload
    let targets = getTargets()

    $(button).addClass('button-disabled')
    await doIf(targets, validateProxy, p => !p.uuid && p.isValid === null)
    await doIf(targets, generatePreviewForProxy, p => !p.previewGenerated && p.isValid)
    await doIf(targets, generateThumbnailForProxy, p => !p.thumbnailGenerated && p.isValid)
    await doIf(targets, generateIconForProxy, p => !p.iconGenerated && p.isValid)
    $(button).removeClass('button-disabled')
}

async function uploadMedia(button) {
    // upload given media to the backend
    let targets = getTargets()

    $(button).addClass('button-disabled')
    await doIf(targets, createItemForProxy, p => !p.uuid)
    await doIf(targets, uploadMetaForProxy, p => !p.metaUploaded && p.uuid)
    await doIf(targets, uploadTagsProxy, p => p.uuid)
    await doIf(targets, saveContentForProxy, p => !p.contentUploaded && p.uuid)
    await doIf(targets, savePreviewForProxy, p => !p.previewUploaded && p.uuid)
    await doIf(targets, saveThumbnailForProxy, p => !p.thumbnailUploaded && p.uuid)
    $(button).removeClass('button-disabled')
}
