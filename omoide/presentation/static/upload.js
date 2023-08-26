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
    'createItemsForProxy',
    'uploadTagsForProxy',
    'uploadPermissionsForProxy',
    'uploadMetainfoForProxy',
    'saveContentForProxy',
    'savePreviewForProxy',
    'saveThumbnailForProxy',
])

let parentProcessed = false
let NUMBER = 1

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
    hideNavButtons()
    UPLOAD_STATE.reset()
}

function addFiles(source) {
    // react on file upload
    showNavButtons()
    let button = $('#media_button')
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

        let proxy = createFileProxy(file, NUMBER)
        NUMBER += 1
        FILES[file.name] = proxy
        local_files.push(proxy)

        proxy.element.deleteElement.click(function () {
            if (confirm(`Are you sure you want ot delete\n${proxy.file.name}?`)) {
                delete FILES[proxy.file.name]
                $('#' + proxy.element.id).remove()
            }
        })

        if (upload_as === 'target') {
            proxy.uuid = parent_uuid
            break
        } else {
            proxy.parent_uuid = parent_uuid
        }
    }

    local_files.sort((a, b) => a.filename > b.filename ? 1 : -1)
    for (let proxy of local_files) {
        proxy.element.element.appendTo(container)
        proxy.render()
    }

    if (local_files) {
        button.removeClass('button-disabled')
    } else {
        button.addClass('button-disabled')
    }

    button.removeClass('upload-in-progress')
    if ($('#auto-continue').is(':checked')) {
        button.click()
    }
}


function extractExt(filename) {
    // extract extension
    let ext = filename.substring(filename.lastIndexOf('.') + 1, filename.length)
    if (!ext)
        return null
    return ext.toLowerCase()
}

class FileProxyElement {
    // Helper object that controls drawing of a file proxy
    constructor(filename, number) {
        this.id = `upload-element-${number}`
        this.element = $('<div>', {
            id: this.id,
            class: 'upload-element'
        })
        this.iconElement = $('<img>', {src: EMPTY_FILE})

        this.progressElement = $('<progress>', {
            id: 'global-progress',
            value: 0,
            max: 100,
        })

        this.textElement = $('<p>', {text: filename})
        this.deleteElement = $('<a>', {
            href: 'javascript:void(0)',
            class: 'button',
        })
        this.deleteLabel = $('<span>', {text: 'Delete'})
        this.deleteElement.append(this.deleteLabel)
        this.linesElement0 = $('<div>', {class: 'upload-lines'})
        this.linesElement1 = $('<div>', {class: 'upload-lines'})

        this.tagsElementLabel = $('<label>',
            {text: 'Additional tags for this item (one tag per line):'})
        this.tagsElement = $('<textarea>', {rows: 5})
        this.tagsElement.appendTo(this.tagsElementLabel)

        this.permissionsElementLabel = $('<label>',
            {text: 'Additional permissions for this item (one user per line):'})
        this.permissionsElement = $('<textarea>', {rows: 5})
        this.permissionsElement.appendTo(this.permissionsElementLabel)

        this.deleteElement.appendTo(this.linesElement1)
        this.textElement.appendTo(this.linesElement1)
        this.progressElement.appendTo(this.linesElement1)
        this.tagsElementLabel.appendTo(this.linesElement1)
        this.permissionsElementLabel.appendTo(this.linesElement1)

        this.iconElement.appendTo(this.linesElement0)
        this.linesElement0.appendTo(this.element)
        this.linesElement1.appendTo(this.element)
    }
}

function createFileProxy(file, number) {
    // create new proxy that stores file upload progress
    let proxy = {
        ready: false,
        uuid: null,
        parentUuid: null,
        isValid: null,
        number: number,

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
            media_type: null,
            content_width: null,
            content_height: null,
            preview_width: null,
            preview_height: null,
            thumbnail_width: null,
            thumbnail_height: null,
            original_file_name: null,
            original_file_modified_at: null,
            features: [],
        },

        // exif
        exif: null,
        exifGenerated: false,
        exifUploaded: false,

        // html
        element: new FileProxyElement(file.name, number),

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
            this.element.iconElement.attr('src', newIcon)
        },
        render: function () {
            this.element.progressElement.val(this.getProgress())
        },
        getTags: function () {
            return this.tagsAdded
        },
        getPermissions: function () {
            return extractAllUUIDs(this.permissionsAdded)
        },
        redrawTags: function () {
            this.element.tagsElement.empty()
            let allTags = this.tagsAdded.join('\n').trim()
            if (allTags.length > 0) {
                allTags += '\n'
            }
            this.element.tagsElement.val(allTags)
        },
    }

    proxy.element.tagsElement.change(function () {
        proxy.tagsAdded = splitLines(proxy.element.tagsElement.val())
    })

    proxy.element.permissionsElement.change(function () {
        proxy.permissionsAdded = splitLines(
            proxy.element.permissionsElement.val()
        )
    })

    proxy.element.iconElement.click(function () {

        if (!proxy.preview)
            return

        if (proxy.previewVisible) {
            proxy.element.iconElement.attr('src', proxy.thumbnail)
            proxy.element.element.css('display', 'grid');
            proxy.element.element.css('flex-direction', 'unset');
            proxy.element.element.css('grid-template-columns', '1fr 3fr');
        } else {
            proxy.element.iconElement.attr('src', proxy.preview)
            proxy.element.element.css('display', 'flex');
            proxy.element.element.css('flex-direction', 'column');
            proxy.element.element.css('grid-template-columns', 'unset');
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

async function createItemsForProxy(targets, uploadState) {
    // send raw data to server and get uuids back
    let progressStorage = new Set([])
    for (let target of targets) {
        if (target.status !== 'fail' && target.uuid) {
            uploadState.setAction(`Creating items`)
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

    if (!targets.length)
        return

    let parent_uuid = targets[0].parent_uuid

    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 10000, // 10 seconds
            type: 'POST',
            url: '/api/items/bulk',
            contentType: 'application/json',
            data: JSON.stringify({
                uuid: null,
                parent_uuid: parent_uuid,
                name: '',
                is_collection: false,
                tags: [],
                permissions: [],
                total: targets.length,
            }),
            success: function (response) {
                if (response.length !== targets.length) {
                    targets.forEach((value, index) => {
                        targets[index].status = 'fail'
                    });
                    reject('fail')
                    return
                }

                for (let i = 0; i < targets.length; i++) {
                    targets[i].uuid = response[i].uuid
                    targets[i].actualSteps.add('createItemsForProxy')
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                for (let i = 0; i < targets.length; i++) {
                    targets[i].status = 'fail'
                }
                reject('fail')
            },
            complete: function () {
                for (let i = 0; i < targets.length; i++) {
                    targets[i].render()
                }
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

async function getImageDimensions(image) {
    // return width, height, resolution
    return new Promise((resolve, reject) => {
        const img = new Image()

        // the following handler will fire after a successful loading of the image
        img.onload = () => {
            const {
                naturalWidth: width,
                naturalHeight: height,
            } = img
            resolve([width, height])
        }

        img.onerror = () => {
            reject('There was some problem with the image.')
        }

        img.src = image
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
                content_width: proxy.metainfo.content_width,
                content_height: proxy.metainfo.content_height,
                preview_width: proxy.metainfo.preview_width,
                preview_height: proxy.metainfo.preview_height,
                thumbnail_width: proxy.metainfo.thumbnail_width,
                thumbnail_height: proxy.metainfo.thumbnail_height,
                content_type: proxy.metainfo.content_type,
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

    let content_width, content_height;
    try {
        [content_width, content_height] = await getImageDimensions(proxy.content)
    } catch (error) {
        [content_width, content_height] = [null, null]
    }
    proxy.metainfo.content_width = content_width
    proxy.metainfo.content_height = content_height


    let preview_width, preview_height;
    try {
        [preview_width, preview_height] = await getImageDimensions(proxy.preview)
    } catch (error) {
        [preview_width, preview_height] = [null, null]
    }
    proxy.metainfo.preview_width = preview_width
    proxy.metainfo.preview_height = preview_height

    let thumbnail_width, thumbnail_height;
    try {
        [thumbnail_width, thumbnail_height] = await getImageDimensions(proxy.thumbnail)
    } catch (error) {
        [thumbnail_width, thumbnail_height] = [null, null]
    }
    proxy.metainfo.thumbnail_width = thumbnail_width
    proxy.metainfo.thumbnail_height = thumbnail_height

    proxy.metainfo.generated = true
    proxy.actualSteps.add('generateMetainfoForProxy')
    proxy.metainfo.user_time = tryGettingUserTime(proxy)
    proxy.metainfo.content_type = proxy.file.type
    proxy.metainfo.original_file_name = proxy.file.name
    proxy.metainfo.original_file_modified_at = lastModified
}

async function generateFeaturesForProxy(proxy, uploadState) {
    // handle additional feature extraction
    if (proxy.featuresGenerated)
        return

    proxy.ready = false
    let useBackoff = $('#feature-exif-backoff').is(':checked')

    if (uploadState.features['extractFeatures']) {
        if (uploadState.features['extractYear'])
            await _extractYearFeature(proxy, useBackoff)

        if (uploadState.features['extractMonthEN'])
            await _extractMonthENFeature(proxy, useBackoff)

        if (uploadState.features['extractMonthRU'])
            await _extractMonthRUFeature(proxy, useBackoff)
    }

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

    if (dt) {
        proxy.tagsAdded.push(extractYearNumberStr(dt))
        proxy.metainfo.features.push('extractYear')
    } else
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
        proxy.metainfo.features.push('extractMonthEN')
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
        proxy.metainfo.features.push('extractMonthRU')
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
            type: 'POST',
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
        await copyContent(parent, firstChild)
        await copyPreview(parent, firstChild)
        await copyThumbnail(parent, firstChild)
        await ensureParentHasThumbnail(parent.parent_uuid, firstChild)
    }
}

async function copyContent(parent, firstChild) {
    // copy content from given child
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 5000, // 5 seconds
            type: 'POST',
            url: `/api/media/${parent.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: firstChild.content,
                media_type: 'content',
                ext: firstChild.contentExt,
            }),
            success: async function (response) {
                resolve(response)
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function copyPreview(parent, firstChild) {
    // copy preview from given child
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 5000, // 5 seconds
            type: 'POST',
            url: `/api/media/${parent.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: firstChild.preview,
                media_type: 'preview',
                ext: firstChild.previewExt,
            }),
            success: async function (response) {
                resolve(response)
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
}

async function copyThumbnail(parent, firstChild) {
    // copy thumbnail from given child
    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 5000, // 5 seconds
            type: 'POST',
            url: `/api/media/${parent.uuid}`,
            contentType: 'application/json',
            data: JSON.stringify({
                content: firstChild.thumbnail,
                media_type: 'thumbnail',
                ext: firstChild.thumbnailExt,
            }),
            success: async function (response) {
                resolve(response)
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                describeFail(XMLHttpRequest.responseJSON)
                reject('fail')
            },
        })
    })
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
                success: async function (response) {
                    await ensureParentIsCollection(parent.parent_uuid)
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

async function uploadTagsForProxy(proxy) {
    // Update item tags as initial + per item
    let tags = [
        ...splitLines($('#item_tags').val()),
        ...proxy.getTags(),
    ]

    if (!tags)
        return

    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 5000, // 5 seconds
            type: 'PUT',
            url: `/api/items/${proxy.uuid}/tags`,
            contentType: 'application/json',
            data: JSON.stringify({'tags': tags}),
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

async function uploadPermissionsProxy(proxy) {
    // Update item permissions as initial + per item
    let permissions = [
        ...extractAllUUIDs(splitLines($('#item_permissions').val())),
        ...proxy.getPermissions(),
    ]

    if (!permissions)
        return

    return new Promise(function (resolve, reject) {
        $.ajax({
            timeout: 5000, // 5 seconds
            type: 'PUT',
            url: `/api/items/${proxy.uuid}/permissions`,
            contentType: 'application/json',
            data: JSON.stringify({
                'apply_to_parents': false,
                'apply_to_children': false,
                'override': true,
                'permissions_before': [],
                'permissions_after': permissions,
            }),
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

async function uploadMedia(button, uploadState) {
    // upload given media to the backend
    let targets = getTargets()
    let handleEXIF = $('#feature-exif').is(':checked')

    if (!targets)
        return

    let upload_as = $('#upload_as')

    $(button).addClass('button-disabled')
    if (upload_as.val() !== 'target') {
        await createItemsForProxy(targets, uploadState)
    }
    await doIf(targets, uploadTagsForProxy, uploadState,
        p => p.uuid && p.isValid)
    await doIf(targets, uploadPermissionsProxy, uploadState,
        p => p.uuid && p.isValid)
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

        if (parent) {
            await ensureParentHasThumbnail(parent, targets[0])

            if (upload_as.val() === 'children') {
                await ensureParentIsCollection(parent)
            }
            parentProcessed = true
        }
    }

    if (allDone()) {
        uploadState.setStatus('uploaded')
        uploadState.setAction('Done uploading')
        uploadState.markDone()

        let uploadSelector = $('#after_upload')

        if (uploadSelector.val() === 'parent') {
            if (upload_as.val() === 'target') {
                let itemItself = await getItem(targets[0].uuid)
                let parentItself = await getItem(itemItself.parent_uuid)

                if (!parentItself)
                    return

                relocateWithAim(`/browse/${parentItself.uuid}`)
            } else if (uploadSelector.val() === 'children'
                && parentUUID !== null) {
                relocateWithAim(`/browse/${parentUUID}`)
            }
        } else if (uploadSelector.val() === 'again') {
            clearProxies()
            uploadState.reset()
            uploadState.setStatus('init')
            uploadState.setAction('Ready for new batch')
            $(button).addClass('button-disabled')
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
        reset: function () {
            // Clear all progress
            this.setStatus('init')
            this.setProgress(0)
            this.setAction('Ready for work')
        },
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
            } else if (this.status === 'uploaded')
                $('#media_button').val('Preprocess media')
        },
        markDone: function () {
            // Save the fact that we uploaded one batch
            let filenames = Object.keys(FILES)
            if (filenames.length !== 0) {
                let first = filenames[filenames.length - 1]
                let last = first

                if (filenames.length > 1) {
                    last = filenames[0]
                }

                let target = $('#media-log')
                let div = $('<div>', {class: 'upload-element upload-lines'})
                div.append($('<h4>', {
                    text: `Total files: ${Object.keys(FILES).length}`
                }))
                div.append($('<hr>'))
                div.append($('<h4>', {
                    text: `First filename: ${first}`
                }))
                div.append($('<h4>', {
                    text: `Last filename: ${last}`
                }))
                div.appendTo(target)
            }
        },
        filenames: {
            first: null,
            last: null,
        },
        features: {
            extractFeatures: false,
            extractYear: true,
            extractMonthEN: false,
            extractMonthRU: true,
        },
        autoContinue: false,
    }
}

function showNavButtons() {
    // Make scrolling buttons visible
    $('#clear-button').show()
    $('#scroll-bottom').show()
    $('#scroll-top').show()
}

function hideNavButtons() {
    // Make scrolling buttons invisible
    $('#clear-button').hide()
    $('#scroll-bottom').hide()
    $('#scroll-top').hide()
}

async function goUpload(button, uploadState) {
    // Main upload pipeline
    if ($('#auto-continue').is(':checked')) {
        if (uploadState.status === 'init') {
            await preprocessMedia(this, uploadState)
            await uploadMedia(this, UPLOAD_STATE)
        } else if (uploadState.status === 'processed') {
            await uploadMedia(this, UPLOAD_STATE)
        }
    } else {
        if (uploadState.status === 'init') {
            await preprocessMedia(this, uploadState)
        } else if (uploadState.status === 'processed') {
            await uploadMedia(this, UPLOAD_STATE)
        }
    }
}
