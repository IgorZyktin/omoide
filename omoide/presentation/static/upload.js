const FILES = {}
const PREVIEW_SIZE = 1024
const THUMBNAIL_SIZE = 384
const EMPTY_FILE = '/static/empty.png'
const VALID_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
const MAX_FILENAME_LENGTH = 255
const EXPECTED_STEPS = new Set([
    'validateProxy',
    'generateContentForProxy',
    'generatePreviewForProxy',
    'generateThumbnailForProxy',
    'generateEXIForProxy',
    'generateFeaturesForProxy',
    'generateMetainfoForProxy',
    'createItemForProxy',
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
    })

    let progressElement = $('<progress>', {
        id: 'global-progress',
        value: 0,
        max: 100,
    })

    let textElement = $('<p>', {
        text: file.name,
    })

    let linesElement0 = $('<div>', {class: 'upload-lines'})
    let linesElement1 = $('<div>', {class: 'upload-lines'})

    let tagsElementLabel = $('<label>',
        {text: 'Additional tags for this item (one tag per line):'})
    let tagsElement = $('<textarea>', {rows: 5})
    tagsElement.appendTo(tagsElementLabel)

    let permissionsElementLabel = $('<label>',
        {text: 'Additional permissions for this item (one user per line):'})
    let permissionsElement = $('<textarea>', {rows: 5})
    permissionsElement.appendTo(permissionsElementLabel)

    textElement.appendTo(linesElement1)
    progressElement.appendTo(linesElement1)
    tagsElementLabel.appendTo(linesElement1)
    permissionsElementLabel.appendTo(linesElement1)

    iconElement.appendTo(linesElement0)
    linesElement0.appendTo(element)
    linesElement1.appendTo(element)
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

        // file
        file: file,
        size: file.size,
        type: file.type,
        filename: file.name,

        // metainfo
        metainfo: {
            generated: false,
            uploaded: false,
            user_time: null,
            width: null,
            height: null,
            resolution: null,
            media_type: null,
            original_file_name: null,
            original_file_modified_at: null,
        },

        // exif
        exif: null,
        exifGenerated: false,
        exifUploaded: false,

        // html
        'element': element,
        'progressElement': progressElement,
        'labelElement': linesElement1,
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

        if (!proxy.preview)
            return

        if (proxy.previewVisible) {
            proxy.iconElement.attr('src', proxy.thumbnail)
            proxy.element.css('display', 'grid');
            proxy.element.css('flex-direction', 'unset');
            proxy.element.css('grid-template-columns', '1fr 3fr');
        } else {
            proxy.iconElement.attr('src', proxy.preview)
            proxy.element.css('display', 'flex');
            proxy.element.css('flex-direction', 'column');
            proxy.element.css('grid-template-columns', 'unset');
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
    else if (handler.name === 'generateEXIForProxy')
        text = `Processing EXIF ${label}`
    else if (handler.name === 'generateFeaturesForProxy')
        text = `Getting info from EXIF ${label}`
    else if (handler.name === 'generateMetainfoForProxy')
        text = `Getting metainfo for ${label}`
    else if (handler.name === 'createItemForProxy')
        text = `Creating item ${label}`
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
    if (!targets.length)
        return

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
                permissions: extractAllUUIDs([
                    ...splitLines($('#item_permissions').val()),
                    ...proxy.getPermissions()
                ]),
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
    proxy.setIcon(proxy.thumbnail)
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

function extractDatetime(rawString) {
    // try to extract datetime from string
    if (!rawString)
        return null

    let parsed = Date.parse(rawString)

    if (isNaN(parsed)) {
        // datetime could be in format "2022:10:29 20:39:00"
        rawString = rawString.replace(':', '-')
        rawString = rawString.replace(':', '-')
    }

    let parsed2 = Date.parse(rawString)
    if (isNaN(parsed2))
        return null

    return rawString
}

function tryGettingUserTime(proxy) {
    // try to extract abstract user time
    let rawTime = extractDatetime(proxy.exif['DateTimeOriginal'])

    if (rawTime) {
        return rawTime.slice(0, 19)
    }
    return null
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
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 10000, // 10 seconds
            type: 'PUT',
            url: `/api/metainfo/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                user_time: proxy.metainfo.user_time,
                width: proxy.metainfo.width,
                height: proxy.metainfo.height,
                duration: null,  // TODO: after we could handle gifs/video
                resolution: proxy.metainfo.resolution,
                media_type: proxy.metainfo.media_type,
                // TODO: add author metainfo to the form
                author: null,
                author_url: null,
                saved_from_url: null,
                description: null,
                extras: {
                    original_file_name: proxy.metainfo.original_file_name,
                    original_file_modified_at: proxy.metainfo.original_file_modified_at,
                },
            }),
            success: function (response) {
                proxy.metainfo.uploaded = true
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

async function generateMetainfoForProxy(proxy, uploadState) {
    // extract file size, dimensions and other metainfo
    let date = new Date(proxy.file.lastModified)
    let lastModified = convertDatetimeToIsoString(date)
    let width, height, resolution;
    try {
        [width, height, resolution] = await getImageDimensions(proxy)
    } catch (error) {
        [width, height, resolution] = [null, null, null]
    }

    proxy.metainfo.generated = true
    proxy.actualSteps.add('generateMetainfoForProxy')
    proxy.metainfo.user_time = tryGettingUserTime(proxy)
    proxy.metainfo.width = width
    proxy.metainfo.height = height
    proxy.metainfo.resolution = resolution
    proxy.metainfo.media_type = proxy.file.type
    proxy.metainfo.original_file_name = proxy.file.name
    proxy.metainfo.original_file_modified_at = lastModified
}

async function generateFeaturesForProxy(proxy, uploadState) {
    // handle additional feature extraction
    proxy.ready = false
    let useBackoff = $('#feature-exif-backoff').is(':checked')

    if (uploadState.features['extractYear'])
        await _extractYearFeature(proxy, useBackoff)

    if (uploadState.features['extractMonthEN'])
        await _extractMonthENFeature(proxy, useBackoff)

    if (uploadState.features['extractMonthRU'])
        await _extractMonthRUFeature(proxy, useBackoff)

    proxy.featuresGenerated = true
    proxy.actualSteps.add('generateFeaturesForProxy')
    proxy.redrawTags()
    proxy.ready = true
}

function extractYearNumberStr(string) {
    // get year from textual DateTime
    return string.slice(0, 4)
}

function extractMonthNumberStr(string) {
    // get month from textual DateTime
    return string.slice(5, 7)
}

function extractDayNumberStr(string) {
    // get day from textual DateTime
    return string.slice(8, 10)
}

async function _extractYearFeature(proxy, useBackoff) {
    // extract year from EXIF tags as a string
    let dt = extractDatetime(proxy.exif['DateTimeOriginal'])

    if (!dt && useBackoff)
        dt = new Date(proxy.file.lastModified).toISOString()

    if (dt)
        proxy.tagsAdded.push(extractYearNumberStr(dt))
    else
        console.log(`No year found for ${proxy.filename}`)
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

async function _extractMonthENFeature(proxy, useBackoff) {
    // extract month from EXIF tags as a string (english)
    let dt = extractDatetime(proxy.exif['DateTimeOriginal'])

    if (!dt && useBackoff)
        dt = new Date(proxy.file.lastModified).toISOString()

    if (dt) {
        let monthName = getMonthNameByNumberEN(extractMonthNumberStr(dt))
        let dayNumber = extractDayNumberStr(dt).replace(/^0+/, '')
        let text = `${monthName} ${dayNumber}`
        proxy.tagsAdded.push(text)
    } else {
        console.log(`No EN month found for ${proxy.filename}`)
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

async function _extractMonthRUFeature(proxy, useBackoff) {
    // extract month from EXIF tags as a string (russian)
    let dt = extractDatetime(proxy.exif['DateTimeOriginal'])

    if (!dt && useBackoff)
        dt = new Date(proxy.file.lastModified).toISOString()

    if (dt) {
        let monthName = getMonthNameByNumberRU(extractMonthNumberStr(dt))
        let dayNumber = extractDayNumberStr(dt).replace(/^0+/, '')
        let text = `${dayNumber} ${monthName}`
        proxy.tagsAdded.push(text)
    } else {
        console.log(`No RU month found for ${proxy.filename}`)
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
                proxy.actualSteps.add('uploadEXIFProxy')
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
            type: 'POST',
            url: `/api/media/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: proxy.content,
                media_type: 'content',
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
            type: 'POST',
            url: `/api/media/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: proxy.preview,
                media_type: 'preview',
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
            type: 'POST',
            url: `/api/media/${proxy.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: proxy.thumbnail,
                media_type: 'thumbnail',
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
    await doIf(targets, generateEXIForProxy, uploadState,
        p => !p.exifGenerated && p.isValid)
    await doIf(targets, generateFeaturesForProxy, uploadState,
        p => !p.featuresGenerated && p.isValid)
    await doIf(targets, generateMetainfoForProxy, uploadState,
        p => !p.metainfo.generated && p.isValid)
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
    await doIf(targets, uploadMetainfoForProxy, uploadState,
        p => !p.metainfo.uploaded && p.uuid && p.isValid)
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
            extractYear: true,
            extractMonthEN: false,
            extractMonthRU: true,
        },
    }
}
