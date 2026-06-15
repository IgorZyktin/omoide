const CARDS = []
let ALL_TAGS = {}

const FEATURE_SCAN_NAME = 'feature-scan-name'
const FEATURE_EXIF_ID = 'feature-exif'
const ALL_FEATURES_EXIF_ID = 'all-features-exif'
const FEATURE_EXIF_TIME_BACKOFF_ID = 'feature-exif-time-backoff'
const FEATURE_EXIF_YEAR_ID = 'feature-exif-year'
const FEATURE_EXIF_MONTH_EN_ID = 'feature-exif-month-en'
const FEATURE_EXIF_MONTH_RU_ID = 'feature-exif-month-ru'

const SCROLL_TOP_ID = 'scroll-top'
const SCROLL_BOTTOM_ID = 'scroll-bottom'
const MEDIA_ID = 'media'
const UPLOAD_INPUT_ID = 'upload-input'

const OWNER_UUID_ID = 'owner-uuid'
const PARENT_UUID_ID = 'parent-uuid'
const GLOBAL_TAGS_ID = 'item-tags'
const GLOBAL_PERMISSIONS_ID = 'item-permissions'
const GLOBAL_PROGRESS_ID = 'global-progress'
const AFTER_UPLOAD_ID = 'after-upload'

const ITEM_CREATION_TIMEOUT = 20000 // 20 seconds
const ITEM_UPLOAD_TIMEOUT = 600000 // 600 seconds

const MONTHS_EN = {
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
}

const MONTHS_RU = {
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
}

const FILENAME_DATE_FORMATS = [
    {regex: /^PXL_(\d{8})_.*/i, parts: m => [m[1].slice(0, 4), m[1].slice(4, 6), m[1].slice(6, 8)]},
    {regex: /^VID_(\d{8})_.*/i, parts: m => [m[1].slice(0, 4), m[1].slice(4, 6), m[1].slice(6, 8)]},
    {regex: /^(\d{4})-(\d{2})-(\d{2}).*/i, parts: m => [m[1], m[2], m[3]]},
]

function toggleExif(checkbox) {
    // Enable/disable nested EXIF sub-features
    const visible = checkbox.checked
    document.getElementById(ALL_FEATURES_EXIF_ID).style.display = visible ? 'block' : 'none'
    for (const id of [
        FEATURE_EXIF_TIME_BACKOFF_ID,
        FEATURE_EXIF_YEAR_ID,
        FEATURE_EXIF_MONTH_EN_ID,
        FEATURE_EXIF_MONTH_RU_ID,
    ]) {
        document.getElementById(id).disabled = !visible
    }
}

function getAllTags() {
    // Return keys of ALL_TAGS sorted by their occurrence counts (desc)
    return Object.keys(ALL_TAGS).sort((a, b) => ALL_TAGS[b] - ALL_TAGS[a])
}

function refreshAllTags() {
    // Clear and rebuild dictionary of known tags
    ALL_TAGS = {}
    const globalTags = splitLines(document.getElementById(GLOBAL_TAGS_ID).value)
    for (const tag of globalTags) {
        ALL_TAGS[tag] = (ALL_TAGS[tag] || 0) + 1
    }

    for (const card of CARDS) {
        for (const tag of card.localTags) {
            ALL_TAGS[tag] = (ALL_TAGS[tag] || 0) + 1
        }
    }
}

function extractEXIFTags(file) {
    // Extract EXIF tags from file. Resolves with {} if no EXIF data.
    return new Promise(resolve => {
        // Cannot use arrow function: EXIF.getAllTags relies on `this`.
        EXIF.getData(file, function () {
            resolve(EXIF.getAllTags(this) || {})
        })
    })
}

function extractDatetime(rawString) {
    // Normalize EXIF datetime ("YYYY:MM:DD HH:MM:SS") into "YYYY-MM-DD HH:MM:SS"
    if (!rawString)
        return null

    // Replace only the date-part colons, leaving the time-part colons intact.
    const normalized = rawString.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3')

    if (isNaN(Date.parse(normalized)))
        return null

    return normalized
}

function extractDateTimeFromFilename(filename) {
    // Try to extract a YYYY-MM-DD date from the filename
    if (!filename)
        return null

    for (const {regex, parts} of FILENAME_DATE_FORMATS) {
        const match = filename.match(regex)
        if (match) {
            const [year, month, day] = parts(match)
            return `${year}-${month}-${day}`
        }
    }

    return null
}

function extractYearNumberStr(string) {
    // get year from textual DateTime (YYYY-MM-DD ...)
    return string.slice(0, 4)
}

function extractMonthNumberStr(string) {
    // get month from textual DateTime (YYYY-MM-DD ...)
    return string.slice(5, 7)
}

function extractDayNumberStr(string) {
    // get day from textual DateTime (YYYY-MM-DD ...)
    return string.slice(8, 10)
}

function extractMonthEN(dt) {
    // Format month as english, e.g. "october 5"
    const monthName = MONTHS_EN[extractMonthNumberStr(dt)] || '???'
    const dayNumber = extractDayNumberStr(dt).replace(/^0+/, '')
    return `${monthName} ${dayNumber}`
}

function extractMonthRU(dt) {
    // Format month as russian, e.g. "5 октября"
    const monthName = MONTHS_RU[extractMonthNumberStr(dt)] || '???'
    const dayNumber = extractDayNumberStr(dt).replace(/^0+/, '')
    return `${dayNumber} ${monthName}`
}

function getFeatures() {
    // Read feature checkboxes and return their values
    const features = {
        scan_name: document.getElementById(FEATURE_SCAN_NAME).checked,
    }

    const exif = document.getElementById(FEATURE_EXIF_ID)
    if (!exif.checked)
        return features

    features.extract_exif = true

    const subFeatures = [
        ['exif_time_backoff', FEATURE_EXIF_TIME_BACKOFF_ID],
        ['exif_year', FEATURE_EXIF_YEAR_ID],
        ['exif_month_en', FEATURE_EXIF_MONTH_EN_ID],
        ['exif_month_ru', FEATURE_EXIF_MONTH_RU_ID],
    ]
    for (const [name, id] of subFeatures) {
        const element = document.getElementById(id)
        if (!element.disabled) {
            features[name] = element.checked
        }
    }

    return features
}

function showNavButtons() {
    document.getElementById(SCROLL_TOP_ID).style.display = 'block'
    document.getElementById(SCROLL_BOTTOM_ID).style.display = 'block'
}

function hideNavButtons() {
    document.getElementById(SCROLL_TOP_ID).style.display = 'none'
    document.getElementById(SCROLL_BOTTOM_ID).style.display = 'none'
}

async function addNewFiles(source, parentUUid) {
    // Create placeholders for added files
    showNavButtons()
    refreshAllTags()
    const media = document.getElementById(MEDIA_ID)
    const features = getFeatures()
    CARDS.length = 0
    media.replaceChildren()
    let number = 1
    for (const file of source.files) {
        const tags = []
        let dt = null

        if (features.scan_name) {
            dt = extractDateTimeFromFilename(file.name)

            if (dt) {
                tags.push(extractMonthRU(dt))
                tags.push(extractYearNumberStr(dt))
            }
        }

        if (features.extract_exif) {
            const exif = await extractEXIFTags(file)
            dt = extractDatetime(exif['DateTimeOriginal'])

            if (!dt && features.exif_time_backoff) {
                dt = new Date(file.lastModified).toISOString()
            }

            if (dt && features.exif_year) {
                tags.push(extractYearNumberStr(dt))
            }

            if (dt && features.exif_month_ru) {
                tags.push(extractMonthRU(dt))
            }

            if (dt && features.exif_month_en) {
                tags.push(extractMonthEN(dt))
            }
        }
        const card = createFileCard(file, parentUUid, number, tags)
        number += 1
        CARDS.push(card)
        console.log(`Added file ${file.name}`)
        media.append(card.element.div)
    }
}

function createFileCard(file, parentUUID, number, tags) {
    // Create new card that stores file upload progress
    const card = {
        uuid: null,
        parentUuid: parentUUID,
        file: file,
        element: new FileCardElement(file, number, tags),
        number: number,
        previewIsVisible: false,
        localTags: [...tags],
        localPermissions: [],
        isFolded: false,

        send() {
            return new Promise(resolve => {
                const xhr = new XMLHttpRequest()
                xhr.timeout = ITEM_UPLOAD_TIMEOUT

                xhr.upload.addEventListener('loadstart', () => {
                    this.element.progress.value = 0
                    this.element.progress.max = 100
                })

                xhr.upload.addEventListener('progress', event => {
                    if (!event.lengthComputable)
                        return
                    const loaded = (event.loaded / event.total) * 100
                    this.element.progress.value = loaded
                    this.element.progress.textContent =
                        `Uploading (${loaded.toFixed(2)}%)…`
                })

                xhr.upload.addEventListener('load', () => {
                    this.element.progress.value = 100
                    this.element.progress.max = 100
                })

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve(xhr.response)
                    } else {
                        this.element.log.textContent =
                            `Upload failed (HTTP ${xhr.status})`
                        console.error(
                            `Upload of ${this.uuid} failed: HTTP ${xhr.status} ${xhr.statusText}`
                        )
                        resolve(undefined)
                    }
                })

                xhr.addEventListener('error', () => {
                    this.element.log.textContent = 'Upload failed'
                    console.error(
                        `An error occurred during the XMLHttpRequest for ${this.uuid}`
                    )
                    resolve(undefined)
                })

                xhr.addEventListener('timeout', () => {
                    this.element.log.textContent = 'Upload timed out'
                    console.error(`Upload of ${this.uuid} timed out`)
                    resolve(undefined)
                })

                xhr.addEventListener('abort', () => {
                    this.element.log.textContent = 'Upload aborted'
                    resolve(undefined)
                })

                const fileData = new FormData()
                fileData.append('file', this.file)

                xhr.open('PUT', `${ITEMS_ENDPOINT}/${this.uuid}/upload`)

                const features = getFeatures()
                for (const [key, value] of Object.entries(features)) {
                    xhr.setRequestHeader(
                        `X-Feature-${key.replaceAll('_', '-')}`, String(value)
                    )
                }
                xhr.setRequestHeader(
                    'X-Feature-Last-Modified',
                    new Date(this.file.lastModified).toISOString(),
                )
                xhr.send(fileData)
            })
        },
    }

    card.element.tagsArea.addEventListener('change', () => {
        card.localTags = splitLines(card.element.tagsArea.value)
    })

    card.element.permissionsArea.addEventListener('change', () => {
        card.localPermissions = extractAllUUIDs(splitLines(
            card.element.permissionsArea.value
        ))
    })

    card.element.fold.addEventListener('click', () => {
        if (card.isFolded) {
            card.element.foldImg.src = '/static/ic_unfold_more_24px.svg'
            card.element.left.style.display = 'flex'
            card.element.right.style.display = 'flex'
            card.element.foldLabel.style.display = 'none'
        } else {
            card.element.foldImg.src = '/static/ic_unfold_less_24px.svg'
            card.element.left.style.display = 'none'
            card.element.right.style.display = 'none'
            card.element.foldLabel.style.display = 'flex'
        }
        card.isFolded = !card.isFolded
    })

    const rebuildTagsDatalist = () => {
        card.element.tagsInputDatalist.replaceChildren()
        for (const tag of getAllTags()) {
            const newVariant = document.createElement('option')
            newVariant.value = tag
            card.element.tagsInputDatalist.append(newVariant)
        }
    }

    card.element.tagsInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            e.preventDefault()
            const textValue = card.element.tagsInput.value.trim()
            if (textValue) {
                card.localTags.push(textValue)
                card.element.tagsArea.value += `${textValue}\n`
                card.element.tagsInput.value = ''
                refreshAllTags()
            }
        }
        rebuildTagsDatalist()
    })

    card.element.tagsInput.addEventListener('click', () => {
        if (card.element.tagsInputDatalist.childElementCount === 0) {
            rebuildTagsDatalist()
        }
    })

    return card
}

class FileCardElement {
    // Helper object that displays file card
    constructor(file, number, tags) {
        this.previewIsVisible = false

        // div itself
        this.div = document.createElement('div')
        this.div.id = `upload-element-${number}`
        this.div.classList.add('upload-element')

        this.foldLabel = document.createElement('h4')
        this.foldLabel.textContent = file.name
        this.foldLabel.style.display = 'none'
        this.div.append(this.foldLabel)

        // left side
        this.left = document.createElement('div')
        this.left.classList.add('upload-lines')
        this.div.append(this.left)

        if (isVideoFile(file)) {
            this.img = document.createElement('video')
        } else {
            this.img = document.createElement('img')
        }
        this.img.src = URL.createObjectURL(file)
        this.img.addEventListener('click', () => this.togglePreview())
        this.left.append(this.img)

        // right side
        this.right = document.createElement('div')
        this.right.classList.add('upload-lines')
        this.div.append(this.right)

        this.foldArea = document.createElement('div')
        this.foldArea.classList.add('float-button-container')
        this.div.append(this.foldArea)

        this.fold = document.createElement('a')
        this.fold.classList.add('float-button')
        this.fold.classList.add('button')
        this.foldArea.append(this.fold)

        this.foldImg = document.createElement('img')
        this.foldImg.src = '/static/ic_unfold_less_24px.svg'
        this.foldImg.style.margin = '0'
        this.fold.append(this.foldImg)

        this.label = document.createElement('h4')
        this.label.textContent = file.name
        this.right.append(this.label)

        this.progress = document.createElement('progress')
        this.progress.value = 0
        this.progress.max = 100
        this.right.append(this.progress)

        if (isVideoFile(file)) {
            this.nameInput = document.createElement('input')
            this.nameInput.type = 'text'
            this.nameInput.placeholder = 'Specify name'
            this.right.append(this.nameInput)
        }

        this.tagsLabel = document.createElement('label')
        this.tagsLabel.append(
            document.createTextNode(
                'Additional tags for this item (one tag per line):'
            )
        )
        this.tagsInput = document.createElement('input')
        this.tagsInput.type = 'text'
        this.tagsInput.placeholder = 'Add tag here'
        this.tagsInput.autocomplete = 'on'
        this.tagsInputDatalist = document.createElement('datalist')
        this.tagsInputDatalist.id = `upload-element-${number}-tags-list`
        this.tagsInput.setAttribute('list', `upload-element-${number}-tags-list`)
        this.tagsInput.append(this.tagsInputDatalist)
        this.tagsArea = document.createElement('textarea')
        this.tagsArea.rows = 5
        this.tagsArea.value = tags.length ? `${tags.join('\n')}\n` : ''
        this.tagsLabel.append(this.tagsArea)
        this.right.append(this.tagsLabel)
        this.right.append(this.tagsInput)

        this.permissionsLabel = document.createElement('label')
        this.permissionsLabel.append(
            document.createTextNode(
                'Additional permissions for this item (one user per line):'
            )
        )
        this.permissionsArea = document.createElement('textarea')
        this.permissionsArea.rows = 5
        this.permissionsArea.value = ''
        this.permissionsLabel.append(this.permissionsArea)
        this.right.append(this.permissionsLabel)

        this.log = document.createElement('div')
        this.div.append(this.log)

        this.delete = document.createElement('a')
        this.delete.textContent = 'Delete'
        this.delete.classList.add('button')
        this.delete.addEventListener('click', () => {
            if (confirm(`Are you sure you want to remove ${file.name} from set?`)) {
                const index = CARDS.findIndex(c => c.number === number)
                if (index !== -1) {
                    CARDS.splice(index, 1)
                }
                this.div.remove()
            }
        })
        this.left.append(this.delete)
    }

    togglePreview() {
        // Make image bigger or smaller
        if (this.previewIsVisible) {
            this.div.style.display = 'grid'
            this.div.style.flexDirection = 'unset'
            this.div.style.gridTemplateColumns = '1fr 3fr'
        } else {
            this.div.style.display = 'flex'
            this.div.style.flexDirection = 'column'
            this.div.style.gridTemplateColumns = 'unset'
        }
        this.previewIsVisible = !this.previewIsVisible
    }

    disable() {
        // Make nested elements disabled
        this.tagsArea.disabled = true
        this.permissionsArea.disabled = true
        this.delete.style.display = 'none'
    }
}

function createItems() {
    // Bulk item creation
    const ownerUUID = document.getElementById(OWNER_UUID_ID).value
    const parentUUID = document.getElementById(PARENT_UUID_ID).value
    const globalTags = splitLines(document.getElementById(GLOBAL_TAGS_ID).value)
    const globalPermissions = extractAllUUIDs(
        splitLines(document.getElementById(GLOBAL_PERMISSIONS_ID).value)
    )

    const arrayForSending = []
    for (const card of CARDS) {
        const localPermissions = []
        for (const uuid of [...globalPermissions, ...card.localPermissions]) {
            localPermissions.push({uuid: uuid, name: ''})
        }

        let name = ''
        if (card.element.nameInput !== undefined) {
            name = card.element.nameInput.value
        }

        arrayForSending.push({
            uuid: null,
            owner_uuid: ownerUUID,
            parent_uuid: parentUUID,
            name: name,
            is_collection: false,
            tags: [...globalTags, ...card.localTags],
            permissions: localPermissions,
        })
    }

    return new Promise(resolve => {
        const xhr = new XMLHttpRequest()
        xhr.timeout = ITEM_CREATION_TIMEOUT
        xhr.responseType = 'json'

        xhr.addEventListener('load', () => {
            if (xhr.status < 200 || xhr.status >= 300) {
                console.error(
                    `Failed to create items: HTTP ${xhr.status} ${xhr.statusText}`,
                    xhr.response,
                )
                resolve(undefined)
                return
            }
            const items = xhr.response?.items ?? []
            for (let i = 0; i < items.length && i < CARDS.length; i++) {
                CARDS[i].uuid = items[i].uuid
            }
            resolve(xhr.response)
        })

        xhr.addEventListener('error', () => {
            console.error('Failed to create items: network error')
            resolve(undefined)
        })

        xhr.addEventListener('timeout', () => {
            console.error('Failed to create items: timeout')
            resolve(undefined)
        })

        xhr.open('POST', `${ITEMS_ENDPOINT}/bulk`)
        xhr.setRequestHeader('Content-Type', 'application/json')
        xhr.send(JSON.stringify(arrayForSending))
    })
}

async function uploadAllFiles() {
    // Perform uploading
    const globalProgress = document.getElementById(GLOBAL_PROGRESS_ID)
    const parentUUID = document.getElementById(PARENT_UUID_ID).value

    const step = CARDS.length ? 100 / CARDS.length : 0
    let progress = 0

    await createItems()

    for (const card of CARDS) {
        if (card.uuid) {
            await card.send()
            progress += step
            globalProgress.value = progress
        } else {
            console.log(`Failed to upload ${card.file.name}, no UUID set`)
        }
    }

    globalProgress.value = 100

    for (const card of CARDS) {
        card.element.disable()
    }
    CARDS.length = 0
    document.getElementById(UPLOAD_INPUT_ID).value = null
    if (document.getElementById(AFTER_UPLOAD_ID).value === 'parent') {
        relocateWithAim(`/browse/${parentUUID}`)
    }
}

function isVideoFile(file) {
    // Return true if file has video content
    return file.name.endsWith('.mp4') || file.name.endsWith('.webm')
}
