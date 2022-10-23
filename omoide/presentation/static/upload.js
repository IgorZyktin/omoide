const FILES = {}
const PREVIEW_SIZE = 1024
const THUMBNAIL_SIZE = 384
const ICON_SIZE = 128
const EMPTY_FILE = '/static/empty.png'
const VALID_EXTENSIONS = ['jpg', 'jpeg']
const MAX_FILENAME_LENGTH = 255
const EXPECTED_STEPS = new Set([
    'validateProxy',
    'generateContentForProxy',
    'generatePreviewForProxy',
    'generateThumbnailForProxy',
    'generateIconForProxy',
    'generateEXIForProxy',
    'generateFeaturesForProxy',
    'createItemForProxy',
    'uploadMetaForProxy',  // TODO: deprecated
    'uploadMetainfoForProxy',
    'saveContentForProxy',
    'savePreviewForProxy',
    'saveThumbnailForProxy',
])

let parentProcessed = false

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
    $('#global-progress').attr('value', 0)
}

function addFiles(source) {
    // react on file upload
    let button = $('#upload_media_button')
    button.addClass('upload-in-progress')

    let parent_uuid = $('#parent_uuid').val() || null
    let container = $('#media')
    let upload_as = $('#upload_as').val()

    if (upload_as === 'target') {
        clearProxies(container)
    }

    let local_files = []

    for (let file of Object.values(source.files)) {
        if (file.name in FILES)
            continue

        let proxy = createFileProxy(file)
        FILES[file.name] = proxy
        local_files.push(proxy)


        if (upload_as === 'target') {
            proxy.uuid = parent_uuid
            break
        } else {
            proxy.parent_uuid = parent_uuid
        }
    }

    local_files.sort((a, b) => a.filename > b.filename ? 1 : -1)
    for (let proxy of local_files) {
        proxy.element.appendTo(container)
        proxy.render()
    }

    let jump = document.createElement('a')
    let linkText = document.createTextNode('Jump to top');
    jump.classList.add('location')  // FIXME
    jump.appendChild(linkText);
    jump.title = 'Scroll back to top';
    jump.onclick = () => {
        document.body.scrollTop = document.documentElement.scrollTop = 0;
    }
    $(jump).appendTo(container)

    button.removeClass('upload-in-progress')
}


function extractExt(filename) {
    // extract extension
    let ext = filename.substring(filename.lastIndexOf('.') + 1, filename.length)
    if (!ext)
        return null
    return ext.toLowerCase()
}

function createFileProxy(file) {
    // create new proxy that stores file upload progress
    let element = $('<div>', {class: 'upload-element'})

    let iconElement = $('<img>', {
        src: EMPTY_FILE,
        width: ICON_SIZE,
        height: 'auto',
    })

    let progressElement = $('<progress>', {
        id: 'global-progress',
        value: 0,
        max: 100,
    })

    let textElement = $('<p>', {
        text: file.name,
    })

    let linesElement = $('<div>', {class: 'upload-lines'})

    let tagsElementLabel = $('<label>',
        {text: 'Additional tags for this item (one tag per line):'})
    let tagsElement = $('<textarea>', {rows: 5})
    tagsElement.appendTo(tagsElementLabel)

    let permissionsElementLabel = $('<label>',
        {text: 'Additional permissions for this item (one user per line):'})
    let permissionsElement = $('<textarea>', {rows: 5})
    permissionsElement.appendTo(permissionsElementLabel)

    textElement.appendTo(linesElement)
    progressElement.appendTo(linesElement)
    tagsElementLabel.appendTo(linesElement)
    permissionsElementLabel.appendTo(linesElement)

    iconElement.appendTo(element)
    linesElement.appendTo(element)
    let proxy = {
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
        previewVisible: false,

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
        // FIXME
        metaUploaded: false,
        metainfoUploaded: false,

        // exif
        exif: null,
        exifGenerated: false,
        exifUploaded: false,

        // html
        'element': element,
        'progressElement': progressElement,
        'labelElement': linesElement,
        'iconElement': iconElement,
        'textElement': textElement,
        'tagsElement': tagsElement,
        'tagsElementLabel': tagsElementLabel,

        features: new Set([]),
        status: 'init',
        description: '',
        actualSteps: new Set([]),
        tagsAdded: [],
        permissionsAdded: [],
        featuresGenerated: false,
        getProgress: function () {
            let _intersection = new Set([]);
            for (let elem of EXPECTED_STEPS) {
                if (this.actualSteps.has(elem))
                    _intersection.add(elem)
            }
            return (_intersection.size / EXPECTED_STEPS.size) * 100
        },
        setIcon: function (newIcon) {
            this.icon = newIcon
            this.iconElement.attr('src', newIcon)
            this.iconElement.css('width', 'auto')
            this.iconGenerated = true
        },
        render: function () {
            this.progressElement.val(this.getProgress())
        },
        getTags: function () {
            return this.tagsAdded
        },
        getPermissions: function () {
            return this.permissionsAdded
        },
        redrawTags: function () {
            this.tagsElement.empty()
            let allTags = this.tagsAdded.join('\n').trim()
            if (allTags.length > 0) {
                allTags += '\n'
            }
            this.tagsElement.val(allTags)
        },
    }

    tagsElement.change(function () {
        proxy.tagsAdded = splitLines(tagsElement.val())
    })

    permissionsElement.change(function () {
        proxy.permissionsAdded = splitLines(permissionsElement.val())
    })

    iconElement.click(function () {

        if (!proxy.icon || !proxy.preview)
            return

        if (proxy.previewVisible) {
            proxy.iconElement.attr('src', proxy.icon)
            proxy.element.css('flex-direction', 'row');
        } else {
            proxy.iconElement.attr('src', proxy.preview)
            proxy.element.css('flex-direction', 'column');
        }

        proxy.previewVisible = !proxy.previewVisible
    })

    return proxy
}

function getHandlerDescription(handler, label) {
    // get human-readable description of current function
    let text

    if (handler.name === 'validateProxy')
        text = `Checking ${label}`
    else if (handler.name === 'generateContentForProxy')
        text = `Processing content ${label}`
    else if (handler.name === 'generatePreviewForProxy')
        text = `Processing preview ${label}`
    else if (handler.name === 'generateThumbnailForProxy')
        text = `Processing thumbnail ${label}`
    else if (handler.name === 'generateIconForProxy')
        text = `Processing icon ${label}`
    else if (handler.name === 'generateEXIForProxy')
        text = `Processing EXIF ${label}`
    else if (handler.name === 'generateFeaturesForProxy')
        text = `Getting info from EXIF ${label}`
    else if (handler.name === 'createItemForProxy')
        text = `Creating item ${label}`
    else if (handler.name === 'uploadMetaForProxy') // TODO: deprecated
        text = `Uploading metainfo ${label}`
    else if (handler.name === 'uploadMetainfoForProxy')
        text = `Uploading metainfo ${label}`
    else if (handler.name === 'uploadPermissionsForProxy')
        text = `Uploading permissions ${label}`
    else if (handler.name === 'uploadEXIFProxy')
        text = `Uploading exif ${label}`
    else if (handler.name === 'saveContentForProxy')
        text = `Uploading content ${label}`
    else if (handler.name === 'savePreviewForProxy')
        text = `Uploading preview ${label}`
    else if (handler.name === 'saveThumbnailForProxy')
        text = `Uploading thumbnail ${label}`
    else
        text = `Doing ${handler.name} for ${label}`

    return text
}

async function doIf(targets, handler, uploadState, condition) {
    // conditionally iterate on every element
    let progressStorage = new Set([])
    for (let target of targets) {
        if (target.status !== 'fail' && condition(target)) {
            let action = getHandlerDescription(handler, target.filename)
            uploadState.setAction(action)
            console.log(action)
            await handler(target, uploadState)
            progressStorage.add(target.getProgress())
        }
    }

    if (!targets.length)
        return

    let totalProgress = 0;
    progressStorage.forEach(num => {
        totalProgress += num;
    });

    if (!isNaN(totalProgress) && totalProgress && progressStorage.size) {
        uploadState.setProgress(totalProgress / progressStorage.size)
    }
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
    proxy.actualSteps.add('validateProxy')
    proxy.render()
}

async function createItemForProxy(proxy) {
    // send raw data to server and get uuid back
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 10000, // 10 seconds
            type: 'POST',
            url: '/api/items',
            contentType: 'application/json',
            data: JSON.stringify({
                parent_uuid: proxy.parent_uuid,
                name: '',
                is_collection: false,
                tags: [
                    ...splitLines($('#item_tags').val()),
                    ...proxy.getTags()
                ],
                permissions: [
                    ...splitLines($('#item_permissions').val()),
                    ...proxy.getPermissions()
                ],
            }),
            success: function (response) {
                proxy.uuid = response['uuid']
                proxy.actualSteps.add('createItemForProxy')
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
    // generate content for proxy
    proxy.ready = false
    proxy.content = await blobToBase64(proxy.file)
    proxy.contentGenerated = true
    proxy.actualSteps.add('generateContentForProxy')
    proxy.ready = true
    proxy.render()
}

async function generatePreviewForProxy(proxy) {
    // generate preview for proxy
    proxy.ready = false
    proxy.preview = await resizeFromFile(proxy.file, PREVIEW_SIZE)
    proxy.previewGenerated = true
    proxy.previewExt = 'jpg'
    proxy.actualSteps.add('generatePreviewForProxy')
    proxy.ready = true
    proxy.render()
}

async function generateThumbnailForProxy(proxy) {
    // generate thumbnail for proxy
    proxy.ready = false
    proxy.thumbnail = await resizeFromFile(proxy.file, THUMBNAIL_SIZE)
    proxy.thumbnailGenerated = true
    proxy.thumbnailExt = 'jpg'
    proxy.actualSteps.add('generateThumbnailForProxy')
    proxy.ready = true
    proxy.render()
}

async function generateIconForProxy(proxy) {
    // generate tiny thumbnail for proxy
    proxy.ready = false
    proxy.setIcon(await resizeFromFile(proxy.file, ICON_SIZE))
    proxy.actualSteps.add('generateIconForProxy')
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
    proxy.actualSteps.add('generateEXIForProxy')
    proxy.ready = true
}

// TODO: deprecated
async function uploadMetaForProxy(proxy) {
    // upload metainfo
    let date = new Date(proxy.file.lastModified)
    let lastModified = convertDatetimeToIsoString(date)
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 10000, // 10 seconds
            type: 'PUT',
            url: `/api/meta/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                original_file_name: proxy.file.name,
                original_file_modified_at: lastModified,
                file_type: proxy.file.type,
                file_size: proxy.file.size,
            }),
            success: function (response) {
                proxy.metaUploaded = true
                proxy.actualSteps.add('uploadMetaForProxy')
                resolve('ok')
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function getImageDimensions(proxy) {
    // return width, height, resolution
    return new Promise((resolve, reject) => {
        const img = new Image()

        // the following handler will fire after a successful loading of the image
        img.onload = () => {
            const {
                naturalWidth: width,
                naturalHeight: height,
            } = img
            let resolution = width * height / 1000000
            resolve([width, height, resolution])
        }

        img.onerror = () => {
            reject('There was some problem with the image.')
        }

        img.src = URL.createObjectURL(proxy.file)
    })
}


async function uploadMetainfoForProxy(proxy) {
    // upload metainfo
    let date = new Date(proxy.file.lastModified)
    let lastModified = convertDatetimeToIsoString(date)
    let width, height, resolution;
    try {
        [width, height, resolution] = await getImageDimensions(proxy)
    } catch (error) {
        [width, height, resolution] = [null, null, null]
    }
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 10000, // 10 seconds
            type: 'PUT',
            url: `/api/metainfo/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                // TODO: abstract time to search on
                user_time: null,
                width: width,
                height: height,
                duration: null,  // TODO: after we could handle gifs/video
                resolution: resolution,
                size: proxy.file.size,
                media_type: proxy.file.type,
                // TODO: add author metainfo to the form
                author: null,
                author_url: null,
                saved_from_url: null,
                description: null,
                extras: {
                    original_file_name: proxy.file.name,
                    original_file_modified_at: lastModified,
                },
            }),
            success: function (response) {
                proxy.metainfoUploaded = true
                proxy.actualSteps.add('uploadMetainfoForProxy')
                resolve('ok')
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function generateFeaturesForProxy(proxy, uploadState) {
    // handle additional feature extraction
    proxy.ready = false

    if (proxy.exif['DateTimeOriginal']) {
        if (uploadState.features['extractYear'])
            await _extractYearFeature(proxy)

        if (uploadState.features['extractMonthEN'])
            await _extractMonthENFeature(proxy)

        if (uploadState.features['extractMonthRU'])
            await _extractMonthRUFeature(proxy)
    } else {
        console.log(`Found no DateTimeOriginal for ${proxy.filename}`)
    }

    proxy.featuresGenerated = true
    proxy.actualSteps.add('generateFeaturesForProxy')
    proxy.redrawTags()
    proxy.ready = true
}

async function _extractYearFeature(proxy) {
    // extract year from EXIF tags as a string
    let year = proxy.exif['DateTimeOriginal'].slice(0, 4)

    if (year)
        proxy.tagsAdded.push(year)
}

function getMonthNameByNumberEN(number) {
    // return month name by its number in english
    return {
        '01': 'january',
        '02': 'february',
        '03': 'march',
        '04': 'april',
        '05': 'may',
        '06': 'june',
        '07': 'july',
        '08': 'august',
        '09': 'september',
        '10': 'october',
        '11': 'november',
        '12': 'december',
    }[number] || '???'
}

async function _extractMonthENFeature(proxy) {
    // extract month from EXIF tags as a string (english)
    let month = proxy.exif['DateTimeOriginal'].slice(5, 7)
    let day = proxy.exif['DateTimeOriginal'].slice(8, 10)

    if (month && day) {
        let dayNumber = day.replace(/^0+/, '')
        let text = `${getMonthNameByNumberEN(month)} ${dayNumber}`
        proxy.tagsAdded.push(text)
    }
}

function getMonthNameByNumberRU(number) {
    // return month name by its number in russian
    return {
        '01': 'января',
        '02': 'февраля',
        '03': 'марта',
        '04': 'апреля',
        '05': 'мая',
        '06': 'июня',
        '07': 'июля',
        '08': 'августа',
        '09': 'сентября',
        '10': 'октября',
        '11': 'ноября',
        '12': 'декабря',
    }[number] || '???'
}

async function _extractMonthRUFeature(proxy) {
    // extract month from EXIF tags as a string (russian)
    let month = proxy.exif['DateTimeOriginal'].slice(5, 7)
    let day = proxy.exif['DateTimeOriginal'].slice(8, 10)

    if (month && day) {
        let dayNumber = day.replace(/^0+/, '')
        let text = `${dayNumber} ${getMonthNameByNumberRU(month)}`
        proxy.tagsAdded.push(text)
    }
}

async function uploadEXIFProxy(proxy) {
    // upload exif data
    if (proxy.exif === null || Object.keys(proxy.exif).length === 0)
        return

    let exif = JSON.parse(clearNullTerminator(JSON.stringify(proxy.exif)))

    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 10000, // 10 seconds
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
            timeout: 100000, // 100 seconds
            type: 'PUT',
            url: `/api/media/${proxy.uuid}/content`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: proxy.content,
                ext: proxy.contentExt,
            }),
            success: function (response) {
                proxy.contentUploaded = true
                proxy.actualSteps.add('saveContentForProxy')
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
            timeout: 100000, // 100 seconds
            type: 'PUT',
            url: `/api/media/${proxy.uuid}/preview`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: proxy.preview,
                ext: proxy.previewExt,
            }),
            success: function (response) {
                proxy.previewUploaded = true
                proxy.actualSteps.add('savePreviewForProxy')
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
            timeout: 100000, // 100 seconds
            type: 'PUT',
            url: `/api/media/${proxy.uuid}/thumbnail`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: proxy.thumbnail,
                ext: proxy.thumbnailExt,
            }),
            success: function (response) {
                proxy.thumbnailUploaded = true
                proxy.actualSteps.add('saveThumbnailForProxy')
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

async function getItem(itemUUID) {
    // load parent by uuid
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 5000, // 5 seconds
            type: 'GET',
            url: `/api/items/${itemUUID}`,
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

async function ensureParentHasThumbnail(parent, firstChild) {
    // use thumbnail of the first child as a parent thumbnail (recursively)
    if (!parent || !firstChild)
        return

    if (typeof parent == 'string')
        parent = await getItem(parent)

    if (parent.thumbnail_ext === null) {
        console.log(`Set parent ${parent.uuid} to use thumbnail from ${firstChild.uuid}`)

        return new Promise(function (resolve, reject) {
            $.ajax({
                timeout: 5000, // 5 seconds
                type: 'PUT',
                url: `/api/media/${parent.uuid}/thumbnail`,
                contentType: 'application/json',
                data: JSON.stringify({
                    content: firstChild.thumbnail,
                    ext: firstChild.thumbnailExt,
                }),
                success: function (response) {
                    ensureParentHasThumbnail(parent.parent_uuid, firstChild)
                    resolve(response)
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    describeFail(XMLHttpRequest.responseJSON)
                    reject('fail')
                },
            })
        })
    }
}


async function ensureParentIsCollection(parent) {
    // mark parent as collection
    if (!parent)
        return

    if (typeof parent == 'string')
        parent = await getItem(parent)

    if (!parent.is_collection) {
        console.log(`Set parent ${parent.uuid} as collection`)

        return new Promise(function (resolve, reject) {
            $.ajax({
                timeout: 5000, // 5 seconds
                type: 'PATCH',
                url: `/api/items/${parent.uuid}`,
                contentType: 'application/json',
                data: JSON.stringify([
                    {
                        'op': 'replace',
                        'path': '/is_collection',
                        'value': true,
                    }
                ]),
                success: function (response) {
                    ensureParentIsCollection(parent.parent_uuid)
                    resolve(response)
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    describeFail(XMLHttpRequest.responseJSON)
                    reject('fail')
                },
            })
        })
    }
}

async function oneShot(button, uploadState) {
    // preprocess + upload
    await preprocessMedia(button, uploadState)
    await uploadMedia(button, uploadState)
}

async function preprocessMedia(button, uploadState) {
    // prepare given media for upload
    let targets = getTargets()

    $(button).addClass('button-disabled')
    await doIf(targets, validateProxy, uploadState,
        p => p.isValid === null)
    await doIf(targets, generateContentForProxy, uploadState,
        p => !p.contentGenerated && p.isValid)
    await doIf(targets, generatePreviewForProxy, uploadState,
        p => !p.previewGenerated && p.isValid)
    await doIf(targets, generateThumbnailForProxy, uploadState,
        p => !p.thumbnailGenerated && p.isValid)
    await doIf(targets, generateIconForProxy, uploadState,
        p => !p.iconGenerated && p.isValid)
    await doIf(targets, generateEXIForProxy, uploadState,
        p => !p.exifGenerated && p.isValid)
    await doIf(targets, generateFeaturesForProxy, uploadState,
        p => !p.featuresGenerated && p.isValid)
    $(button).removeClass('button-disabled')

    uploadState.setAction('Done processing')
    uploadState.setStatus('processed')
}

async function uploadMedia(button, uploadState) {
    // upload given media to the backend
    let targets = getTargets()
    let handleEXIF = $('#feature-exif').is(':checked')

    $(button).addClass('button-disabled')
    await doIf(targets, createItemForProxy, uploadState,
        p => !p.uuid && p.isValid)
    // TODO: deprecated
    await doIf(targets, uploadMetaForProxy, uploadState,
        p => !p.metaUploaded && p.uuid && p.isValid)
    await doIf(targets, uploadMetainfoForProxy, uploadState,
        p => !p.metainfoUploaded && p.uuid && p.isValid)
    await doIf(targets, uploadEXIFProxy, uploadState,
        p => !p.exifUploaded && p.uuid && p.isValid && handleEXIF)
    await doIf(targets, saveContentForProxy, uploadState,
        p => !p.contentUploaded && p.uuid && p.isValid)
    await doIf(targets, savePreviewForProxy, uploadState,
        p => !p.previewUploaded && p.uuid && p.isValid)
    await doIf(targets, saveThumbnailForProxy, uploadState,
        p => !p.thumbnailUploaded && p.uuid && p.isValid)
    $(button).removeClass('button-disabled')

    let parentUUID = $('#parent_uuid').val() || null

    if (!parentProcessed && parentUUID) {
        let parent = await getItem(parentUUID)

        if (parent !== undefined) {
            await ensureParentHasThumbnail(parent, targets[0])

            if ($('#upload_as').val() === 'children') {
                await ensureParentIsCollection(parent)
            }
            parentProcessed = true
        }
    }

    if (allDone()) {
        uploadState.setStatus('uploaded')
        uploadState.setAction('Done uploading')

        if ($('#after_upload').val() === 'parent'
            && parentUUID !== null) {
            relocateWithAim(`/browse/${parentUUID}`)
        }
    }
}

function createUploadState(divId) {
    // progress of upload, goes init -> processed -> uploaded
    let element = $('#' + divId)

    let progressElement = $('<progress>', {
        id: 'global-progress',
        value: 0,
        max: 100,
    })

    let labelElement = $('<label>', {
        id: 'test',
        text: 'Completion: 0.00%'
    })
    labelElement.attr('for', 'global-progress')

    let actionElement = $('<span>', {
        text: 'Ready for work'
    })

    labelElement.appendTo(element)
    progressElement.appendTo(element)
    actionElement.appendTo(element)
    return {
        status: 'init',
        element: element,
        progress: 0,
        action: 'Ready for work',
        progressElement: progressElement,
        labelElement: labelElement,
        actionElement: actionElement,
        setAction: function (newAction) {
            this.action = newAction
            this.actionElement.text(newAction)
        },
        setProgress: function (newProgress) {
            this.progress = newProgress
            this.progressElement.val(newProgress)
            this.labelElement.text(`Completion: ${newProgress.toFixed(2)}%`)
        },
        setStatus: function (newStatus) {
            this.status = newStatus

            if (this.status === 'processed') {
                $('#media_button').val('Upload media')
            }
        },
        features: {
            extractYear: false,
            extractMonthEN: false,
            extractMonthRU: false,
        },
    }
}
