const CARDS = []

const FEATURE_EXIF_ID = "feature-exif"
const ALL_FEATURES_EXIF_ID = "all-features-exif"
const FEATURE_EXIF_TIME_BACKOFF_ID = "feature-exif-time-backoff"
const FEATURE_EXIF_YEAR_ID = "feature-exif-year"
const FEATURE_EXIF_MONTH_EN_ID = "feature-exif-month-en"
const FEATURE_EXIF_MONTH_RU_ID = "feature-exif-month-ru"

const SCROLL_TOP_ID = "scroll-top"
const SCROLL_BOTTOM_ID = "scroll-bottom"
const MEDIA_ID = "media"

const OWNER_UUID_ID = "owner-uuid"
const PARENT_UUID_ID = "parent-uuid"
const GLOBAL_TAGS_ID = "item-tags"
const GLOBAL_PERMISSIONS_ID = "item-permissions"
const GLOBAL_PROGRESS_ID = "global-progress"
const AFTER_UPLOAD_ID = "after-upload"

const SEND_TIMEOUT = 20000 // 20 seconds

function toggleExif(checkbox) {
    // Make exif switches enabled/disabled
    if (checkbox.checked) {
        document.getElementById(ALL_FEATURES_EXIF_ID).style.display = "block";
        document.getElementById(FEATURE_EXIF_TIME_BACKOFF_ID).disabled = false
        document.getElementById(FEATURE_EXIF_YEAR_ID).disabled = false
        document.getElementById(FEATURE_EXIF_MONTH_EN_ID).disabled = false
        document.getElementById(FEATURE_EXIF_MONTH_RU_ID).disabled = false
    } else {
        document.getElementById(ALL_FEATURES_EXIF_ID).style.display = "none";
        document.getElementById(FEATURE_EXIF_TIME_BACKOFF_ID).disabled = true
        document.getElementById(FEATURE_EXIF_YEAR_ID).disabled = true
        document.getElementById(FEATURE_EXIF_MONTH_EN_ID).disabled = true
        document.getElementById(FEATURE_EXIF_MONTH_RU_ID).disabled = true
    }
}

async function extractEXIFTags(file) {
    // Extract tags from file
    return new Promise(function (resolve, _) {
        EXIF.getData(file, function () {
            resolve(EXIF.getAllTags(this))
        })
    })
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

function getMonthNameByNumberEN(number) {
    // Return month name by its number in english
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

function extractMonthEN(dt) {
    // Extract month from EXIF tags as a string (english)
    let monthName = getMonthNameByNumberEN(extractMonthNumberStr(dt))
    let dayNumber = extractDayNumberStr(dt).replace(/^0+/, '')
    return `${monthName} ${dayNumber}`
}

function getMonthNameByNumberRU(number) {
    // Return month name by its number in russian
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

function extractMonthRU(dt) {
    // Extract month from EXIF tags as a string (russian)
    let monthName = getMonthNameByNumberRU(extractMonthNumberStr(dt))
    let dayNumber = extractDayNumberStr(dt).replace(/^0+/, '')
    return `${dayNumber} ${monthName}`
}

function splitLines(text) {
    // split string by line separators and return only non-empty
    return text.replace(/\r\n/, '\n').split('\n').filter(n => n)
}

function getFeatures() {
    // Read feature checkboxes and return their values
    let exif = document.getElementById(FEATURE_EXIF_ID)

    if (!exif.checked)
        return {}

    let features = {extract_exif: true}

    let exifTimeBackoff = document.getElementById(FEATURE_EXIF_TIME_BACKOFF_ID)
    if (!exifTimeBackoff.disabled)
        features["exif_time_backoff"] = exifTimeBackoff.checked

    let exifYear = document.getElementById(FEATURE_EXIF_YEAR_ID)
    if (!exifYear.disabled)
        features["exif_year"] = exifYear.checked

    let exifMonthEn = document.getElementById(FEATURE_EXIF_MONTH_EN_ID)
    if (!exifMonthEn.disabled)
        features["exif_month_en"] = exifMonthEn.checked

    let exifMonthRu = document.getElementById(FEATURE_EXIF_MONTH_RU_ID)
    if (!exifMonthRu.disabled)
        features["exif_month_ru"] = exifMonthRu.checked

    return features
}

function showNavButtons() {
    // Make scrolling buttons visible
    document.getElementById(SCROLL_TOP_ID).style.display = "block"
    document.getElementById(SCROLL_BOTTOM_ID).style.display = "block"
}

function hideNavButtons() {
    // Make scrolling buttons invisible
    document.getElementById(SCROLL_TOP_ID).style.display = "none"
    document.getElementById(SCROLL_BOTTOM_ID).style.display = "none"
}

async function addNewFiles(source, parentUUid) {
    // Create placeholders for added files
    showNavButtons()
    let media = document.getElementById(MEDIA_ID)
    let features = getFeatures()
    CARDS.length = 0
    media.replaceChildren()
    let number = 1
    for (let file of Object.values(source.files)) {
        let tags = []
        let exif
        if (features.extract_exif) {
            await extractEXIFTags(file).then(function (result) {
                exif = result
            })
            let dt = extractDatetime(exif['DateTimeOriginal'])

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
        let card = createFileCard(file, parentUUid, number, tags)
        number += 1
        CARDS.push(card)
        console.log(`Added file ${file.name}`)
        media.append(card.element.div)
    }
}

function createFileCard(file, parentUUID, number, tags) {
    // Create new card that stores file upload progress
    let card = {
        uuid: null,
        parentUuid: parentUUID,
        file: file,
        element: new FileCardElement(file, number, tags),
        number: number,
        previewIsVisible: false,
        localTags: [...tags],
        localPermissions: [],

        send: async function (thisCard) {
            let promise = new Promise(resolve => {
                const xhr = new XMLHttpRequest()
                xhr.timeout = SEND_TIMEOUT

                xhr.upload.addEventListener("loadstart", (event) => {
                    this.element.progress.value = 0
                    this.element.progress.max = event.total
                });

                xhr.upload.addEventListener("progress", (event) => {
                    this.element.progress.value = event.loaded;
                    this.element.progress.textContent = `Uploading (${(
                        (event.loaded / event.total) *
                        100
                    ).toFixed(2)}%)…`;
                });

                xhr.upload.addEventListener("loaded", (event) => {
                    this.element.progress.value = 100
                    this.element.progress.max = 100
                });

                xhr.onload = function (e) {
                    resolve(xhr.response);
                };
                xhr.onerror = function () {
                    resolve(undefined);
                    thisCard.element.log.textContent = "Upload failed"
                    console.error(`An error occurred during the XMLHttpRequest for ${thisCard.uuid}`)
                };

                const fileData = new FormData();
                fileData.append("file", file);

                xhr.open("PUT", `${ITEMS_ENDPOINT}/${this.uuid}/upload`, true)

                let features = getFeatures()
                for (const [key, value] of Object.entries(features)) {
                    xhr.setRequestHeader(`X-Feature-${key.replaceAll('_', '-')}`, value)
                }
                xhr.setRequestHeader('X-Feature-Last-Modified', this.file.lastModifiedDate.toISOString())
                xhr.send(fileData);
                return xhr
            })
            return await promise
        },
    }

    card.element.tagsArea.addEventListener("change", function () {
        card.localTags = splitLines(card.element.tagsArea.value)
    })

    card.element.permissionsArea.addEventListener("change", function () {
        card.localPermissions = extractAllUUIDs(splitLines(
            card.element.permissionsArea.value
        ))
    })
    return card
}

class FileCardElement {
    // Helper object that displays file card
    constructor(file, number, tags) {
        this.previewIsVisible = false

        // div itself
        this.div = document.createElement("div")
        this.div.id = `upload-element-${number}`
        this.div.classList.add("upload-element")

        // left side
        this.left = document.createElement("div");
        this.left.classList.add("upload-lines")
        this.div.append(this.left)

        this.img = document.createElement("img")
        this.img.src = URL.createObjectURL(file)
        this.img.addEventListener("click", () => this.togglePreview())
        this.left.append(this.img)

        // right side
        this.right = document.createElement("div");
        this.right.classList.add("upload-lines")
        this.div.append(this.right)

        this.label = document.createElement("h4")
        this.label.innerHTML = file.name
        this.right.append(this.label)

        this.progress = document.createElement("progress")
        this.progress.value = 0
        this.progress.max = 100
        this.right.append(this.progress)

        this.tagsLabel = document.createElement("label")
        this.tagsLabel.innerHTML = "Additional tags for this item (one tag per line):"
        this.tagsArea = document.createElement("textarea")
        this.tagsArea.rows = 5
        this.tagsArea.innerHTML = tags.join('\n')
        this.tagsLabel.append(this.tagsArea)
        this.right.append(this.tagsLabel)

        this.permissionsLabel = document.createElement("label")
        this.permissionsLabel.innerHTML = "Additional permissions for this item (one user per line):"
        this.permissionsArea = document.createElement("textarea")
        this.permissionsArea.rows = 5
        this.permissionsLabel.append(this.permissionsArea)
        this.right.append(this.permissionsLabel)

        this.log = document.createElement("div");
        this.div.append(this.log)

        this.delete = document.createElement("a")
        this.delete.innerHTML = "Delete"
        this.delete.classList.add("button")
        this.delete.addEventListener("click", function () {
            if (confirm(`Are you sure you want to remove ${file.name} from set?`)) {
                for (let i = CARDS.length - 1; i >= 0; i--) {
                    if (CARDS[i].number === number) {
                        CARDS.splice(i, 1);
                        break
                    }
                }
                document.getElementById(`upload-element-${number}`).remove();
            }
        })
        this.left.append(this.delete)
    }

    togglePreview() {
        // Make image bigger or smaller
        if (this.previewIsVisible) {
            this.div.style.display = "grid"
            this.div.style.flexDirection = "unset"
            this.div.style.gridTemplateColumns = "1fr 3fr"
        } else {
            this.div.style.display = "flex"
            this.div.style.flexDirection = "column"
            this.div.style.gridTemplateColumns = "unset"
        }
        this.previewIsVisible = !this.previewIsVisible
    }

    disable() {
        // Make nested elements disabled
        this.tagsArea.disabled = true
        this.permissionsArea.disabled = true
        this.delete.style.display = "none"
    }
}

async function createItems() {
    // Bulk item creation
    let ownerUUID = document.getElementById(OWNER_UUID_ID).value
    let parentUUID = document.getElementById(PARENT_UUID_ID).value
    let globalTags = splitLines(document.getElementById(GLOBAL_TAGS_ID).value)
    let globalPermissions = extractAllUUIDs(
        splitLines(document.getElementById(GLOBAL_PERMISSIONS_ID).value)
    )

    let arrayForSending = []
    for (let card of CARDS) {
        let localPermissions = []
        for (const uuid of [...globalPermissions, ...card.localPermissions]) {
            localPermissions.push({uuid: uuid, name: ''})
        }
        arrayForSending.push({
            uuid: null,
            owner_uuid: ownerUUID,
            parent_uuid: parentUUID,
            name: '',
            is_collection: false,
            tags: [...globalTags, ...card.localTags],
            permissions: localPermissions,
        })
    }

    let promise = new Promise(resolve => {
        const xhr = new XMLHttpRequest()
        xhr.timeout = SEND_TIMEOUT
        xhr.responseType = "json";

        xhr.onload = function (e) {
            resolve(xhr.response);
            for (let i = 0; i < xhr.response["items"].length; i++) {
                CARDS[i].uuid = xhr.response["items"][i]["uuid"]
            }
        };

        xhr.onerror = function () {
            resolve(undefined);
            console.error("Failed to create items")
        };

        xhr.open("POST", `${ITEMS_ENDPOINT}/bulk`, true)
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify(arrayForSending))
        return xhr
    })
    return await promise
}

async function uploadAllFiles() {
    // Perform uploading
    let globalProgress = document.getElementById(GLOBAL_PROGRESS_ID).value
    let parentUUID = document.getElementById(PARENT_UUID_ID).value

    let step = 0
    let progress = 0
    if (CARDS.length) {
        step = CARDS.length / 100
    }

    await createItems()

    for (let card of CARDS) {
        if (card.uuid) {
            await card.send(card)
            progress += step
            globalProgress.value = progress
        } else {
            console.log(`Failed to upload ${card.file.name}, no UUID set`)
        }
    }

    globalProgress.value = 0

    for (let card of CARDS) {
        card.element.disable()
    }
    CARDS.length = 0
    document.getElementById("upload-input").value = null
    if (document.getElementById(AFTER_UPLOAD_ID).value === 'parent') {
        relocateWithAim(`/browse/${parentUUID}`)
    }
}
