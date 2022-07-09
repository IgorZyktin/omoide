const FILES = {}
const PREVIEW_SIZE = 1024
const THUMBNAIL_SIZE = 384
const ICON_SIZE = 128
const EMPTY_FILE = '/static/empty.png'
const TOTAL_STEPS = 10
const VALID_EXTENSIONS = ['jpg', 'jpeg']

let reducer = new window.ImageBlobReduce({
    pica: window.ImageBlobReduce.pica({features: ['js', 'wasm', 'ww']})
});

reducer._calculate_size = function (env) {
    let dimension = Math.min(env.opts.max, env.image.height)
    let coefficient = dimension / env.image.height
    env.transform_width = Math.ceil(coefficient * env.image.width)
    env.transform_height = dimension
    return env;
};

reducer._create_blob = function (env) {
    return this.pica.toBlob(env.out_canvas, 'image/jpeg', 0.75)
        .then(function (blob) {
            env.out_blob = blob;
            return env;
        });
};

async function blobToBase64(blob) {
    return new Promise((resolve, _) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.readAsDataURL(blob);
    });
}

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

        proxy.parent_uuid = parent_uuid
        proxy.element.appendTo(container)
        proxy.render()
    }

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
        uuid: null,
        parentUuid: null,
        isValid: null,

        // content
        content: null,
        contentExt: extractExt(file.name),
        contentGenerated: false,
        contentUploaded: false,

        // preview
        preview: null,
        previewExt: null,
        previewGenerated: false,
        previewUploaded: false,

        // thumbnail
        thumbnail: null,
        thumbnailExt: null,
        thumbnailGenerated: false,
        thumbnailUploaded: false,

        // icon
        icon: null,
        iconGenerated: false,

        // file
        file: file,
        size: file.size,
        type: file.type,
        filename: file.name,

        // meta
        metaUploaded: false,

        // exif
        exifUploaded: false,

        updatedAt: file.lastModified,
        element: $('<div>', {class: 'upload-element'}),
        features: [],
        status: 'init',
        description: '',
        steps: 0,
        totalSteps: TOTAL_STEPS,  // tags are not counted as a step
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

    if (!VALID_EXTENSIONS.includes(proxy.contentExt)) {
        proxy.status = 'fail'
        proxy.isValid = false
        makeAlert(`File extension must be one of: ${VALID_EXTENSIONS}`)
    }

    if (proxy.contentExt === 'jpeg') {
        proxy.contentExt = 'jpg'
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

async function resizeFromFile(file, maxSize) {
    // generate smaller version of the image using original file
    return reducer
        .toBlob(
            file,
            {
                max: maxSize,
                unsharpAmount: 80,
                unsharpRadius: 0.6,
                unsharpThreshold: 2
            }
        )
        .then(blob => blobToBase64(blob))
}

async function generateContentForProxy(proxy) {
    // generate preview for proxy
    proxy.ready = false
    proxy.content = await blobToBase64(proxy.file)
    proxy.contentGenerated = true
    proxy.steps += 1
    proxy.ready = true
    proxy.render()
}

async function generatePreviewForProxy(proxy) {
    // generate preview for proxy
    proxy.ready = false
    proxy.preview = await resizeFromFile(proxy.file, PREVIEW_SIZE)
    proxy.previewGenerated = true
    proxy.previewExt = 'jpg'
    proxy.steps += 1
    proxy.ready = true
    proxy.render()
}

async function generateThumbnailForProxy(proxy) {
    // generate thumbnail for proxy
    proxy.ready = false
    proxy.thumbnail = await resizeFromFile(proxy.file, THUMBNAIL_SIZE)
    proxy.thumbnailGenerated = true
    proxy.thumbnailExt = 'jpg'
    proxy.steps += 1
    proxy.ready = true
    proxy.render()
}

async function generateIconForProxy(proxy) {
    // generate tiny thumbnail for proxy
    proxy.ready = false
    proxy.icon = await resizeFromFile(proxy.file, ICON_SIZE)
    proxy.iconGenerated = true
    proxy.steps += 1
    proxy.ready = true
    proxy.render()
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

    return new Promise(function (resolve, reject) {
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
                reject('fail')
            },
            complete: function () {
                resolve('ok')
                proxy.render()
            },
        })
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
                content: proxy.preview,
                ext: proxy.previewExt,
            }),
            success: function (response) {
                proxy.previewUploaded = true
                proxy.steps += 1
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
            complete: function () {
                resolve('ok')
                proxy.render()
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
                content: proxy.thumbnail,
                ext: proxy.thumbnailExt,
            }),
            success: function (response) {
                proxy.thumbnailUploaded = true
                proxy.steps += 1
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
            complete: function () {
                resolve('ok')
                proxy.render()
            },
        })
    })
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
    await doIf(targets, generateContentForProxy, p => !p.contentGenerated && p.isValid)
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
