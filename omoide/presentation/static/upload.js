const FILES = {}
const PREVIEW_SIZE = 1024
const THUMBNAIL_SIZE = 384
const ICON_SIZE = 128
const EMPTY_FILE = '/static/empty.png'
const TOTAL_STEPS = 11
const VALID_EXTENSIONS = ['jpg', 'jpeg']
const MAX_FILENAME_LENGTH = 255

let parentThumbnailUploaded = false

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

function clearProxies() {
    // delete all possible proxies
    Object.keys(FILES).forEach(key => {
        delete FILES[key];
    })
    $('#media').empty()
}

function addFiles(source) {
    // react on file upload
    let button = $('#upload_media_button')
    button.addClass('upload-in-progress')

    let parent_uuid = $('#parent_uuid').val() || null
    let tags = splitLines($('#item_tags').val())
    let container = $('#media')
    let upload_as = $('#upload_as').val()

    if (upload_as === 'target') {
        clearProxies(container)
    }

    for (let file of Object.values(source.files)) {
        if (file.name in FILES)
            continue

        let proxy = createFileProxy(file, tags)
        FILES[file.name] = proxy

        proxy.element.appendTo(container)
        proxy.render()

        if (upload_as === 'target') {
            proxy.uuid = parent_uuid
            break
        } else {
            proxy.parent_uuid = parent_uuid
        }
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
        exif: null,
        exifGenerated: false,
        exifUploaded: false,

        updatedAt: file.lastModified,
        element: $('<div>', {class: 'upload-element'}),
        features: [],
        status: 'init',
        description: '',
        steps: 0,
        totalSteps: TOTAL_STEPS,
        tagsInitial: tags,
        tagsUploaded: false,
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
        getTags: function () {
            return this.tagsInitial
        }
    }
}

async function doIf(targets, handler, condition) {
    // conditionally iterate on every element
    let progress = 0
    for (let target of targets) {
        if (target.status !== 'fail' && condition(target)) {
            let label = target.uuid || target.file.name
            console.log(`Doing ${handler.name} for ${label}`)
            await handler(target)
            progress += target.getProgress()
        }
    }

    if (!targets.length)
        return

    $('#global-progress').attr('value', progress / targets.length)
}

async function validateProxy(proxy) {
    // ensure that content is adequate
    if (proxy.filename.length > MAX_FILENAME_LENGTH) {
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
                tags: proxy.getTags(),
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

async function extractEXIFTags(file) {
    // extract tags from file
    return new Promise(function (resolve, _) {
        EXIF.getData(file, function () {
            resolve(EXIF.getAllTags(this))
        })
    })
}

function clearNullTerminator(string) {
    // remove u0 symbols
    return string.replace(/\\u([0-9]|[a-fA-F])([0-9]|[a-fA-F])([0-9]|[a-fA-F])([0-9]|[a-fA-F])/g, "")
}

async function generateEXIForProxy(proxy) {
    // extract exif tags
    proxy.ready = false

    let exif
    await extractEXIFTags(proxy.file).then(function (result) {
        exif = result
    })

    proxy.exif = exif
    proxy.exifGenerated = true
    proxy.ready = true
}

async function uploadMetaForProxy(proxy) {
    // upload metainfo
    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'PUT',
            url: `/api/meta/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                original_file_name: proxy.file.name,
                original_file_modified_at: proxy.file.lastModified,
                file_type: proxy.file.type,
                file_size: proxy.file.size,
            }),
            success: function (response) {
                proxy.metaUploaded = true
                proxy.steps += 1
                resolve('ok')
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function uploadTagsProxy(proxy) {
    // upload tags
    // TODO - add tags upload
    proxy.tagsUploaded = true
    proxy.steps += 1
}

async function uploadEXIFProxy(proxy) {
    // upload exif data
    if (proxy.exif === null || Object.keys(proxy.exif).length === 0)
        return

    let exif = JSON.parse(clearNullTerminator(JSON.stringify(proxy.exif)))

    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'PUT',
            url: `/api/exif/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                exif: exif,
            }),
            success: function (response) {
                proxy.exifUploaded = true
                resolve('ok')
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function saveContentForProxy(proxy) {
    // save content of the proxy on the server
    if (!proxy.content || proxy.contentUploaded)
        return

    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'PUT',
            url: `/api/media/${proxy.uuid}/content`,
            contentType: 'application/json',
            data: JSON.stringify({
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
            url: `/api/media/${proxy.uuid}/preview`,
            contentType: 'application/json',
            data: JSON.stringify({
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
            url: `/api/media/${proxy.uuid}/thumbnail`,
            contentType: 'application/json',
            data: JSON.stringify({
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

    if ($('#upload_as').val() === 'children') {
        targets = Object.values(FILES)
        targets.sort((a, b) => a.filename > b.filename ? 1 : -1)
    } else {
        if (Object.keys(FILES).length) {
            targets = [Object.values(FILES)[0]]
        } else {
            targets = []
        }
    }

    return targets
}

function allDone() {
    // return true if all items are ready
    for (let proxy of Object.values(FILES)) {
        let done = proxy.isValid
            && proxy.uuid
            && proxy.contentUploaded
            && proxy.previewUploaded
            && proxy.thumbnailUploaded

        if (!done) {
            return false
        }
    }
    return true
}

async function getParent(parentUUID) {
    // load parent by uuid
    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'GET',
            url: `/api/items/${parentUUID}`,
            contentType: 'application/json',
            success: function (response) {
                resolve(response)
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function ensureParentHasThumbnail(parentUUID, targets) {
    // use thumbnail of the first child as a parent thumbnail
    if (!parentUUID || !targets.length || parentThumbnailUploaded)
        return

    let parent

    await getParent(parentUUID).then(function (result) {
        parent = result
    })

    let firstChild = targets[0]

    if (!parent || !firstChild)
        return

    if (parent.thumbnail_ext === null) {
        console.log(`Set parent ${parentUUID} to use thumbnail from ${firstChild.uuid}`)

        return new Promise(function (resolve, reject) {
            $.ajax({
                type: 'PUT',
                url: `/api/media/${parentUUID}/thumbnail`,
                contentType: 'application/json',
                data: JSON.stringify({
                    content: firstChild.thumbnail,
                    ext: firstChild.thumbnailExt,
                }),
                success: function (response) {
                    parentThumbnailUploaded = true
                    resolve('ok')
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    describeFail(XMLHttpRequest.responseJSON)
                    reject('fail')
                },
            })
        })
    }
}

async function preprocessMedia(button) {
    // prepare given media for upload
    let targets = getTargets()

    $(button).addClass('button-disabled')
    await doIf(targets, validateProxy, p => p.isValid === null)
    await doIf(targets, generateContentForProxy, p => !p.contentGenerated && p.isValid)
    await doIf(targets, generatePreviewForProxy, p => !p.previewGenerated && p.isValid)
    await doIf(targets, generateThumbnailForProxy, p => !p.thumbnailGenerated && p.isValid)
    await doIf(targets, generateIconForProxy, p => !p.iconGenerated && p.isValid)
    await doIf(targets, generateEXIForProxy, p => !p.exifGenerated && p.isValid)
    $(button).removeClass('button-disabled')
}

async function uploadMedia(button) {
    // upload given media to the backend
    let targets = getTargets()
    let handleEXIF = $('#feature-exif').is(':checked')

    $(button).addClass('button-disabled')
    await doIf(targets, createItemForProxy, p => !p.uuid && p.isValid)
    await doIf(targets, uploadMetaForProxy, p => !p.metaUploaded && p.uuid && p.isValid)
    await doIf(targets, uploadTagsProxy, p => !p.tagsUploaded && p.uuid && p.isValid)
    await doIf(targets, uploadEXIFProxy, p => !p.exifUploaded && p.uuid && p.isValid && handleEXIF)
    await doIf(targets, saveContentForProxy, p => !p.contentUploaded && p.uuid && p.isValid)
    await doIf(targets, savePreviewForProxy, p => !p.previewUploaded && p.uuid && p.isValid)
    await doIf(targets, saveThumbnailForProxy, p => !p.thumbnailUploaded && p.uuid && p.isValid)
    $(button).removeClass('button-disabled')

    let parent_uuid = $('#parent_uuid').val() || null
    // TODO - what if parent of the parent has no thumbnail?
    await ensureParentHasThumbnail(parent_uuid, targets)

    if (allDone()
        && $('#after_upload').val() === 'parent'
        && parent_uuid !== null) {
        relocateWithAim(`/browse/${parent_uuid}`)
    }
}
