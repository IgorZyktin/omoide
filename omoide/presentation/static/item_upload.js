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

function addNewFiles(source, parentUUid) {
    // Create placeholders for added files
    showNavButtons()
    let media = document.getElementById(MEDIA_ID)
    CARDS.length = 0
    media.replaceChildren()
    let number = 1
    for (let file of Object.values(source.files)) {
        let card = createFileCard(file, parentUUid, number)
        number += 1
        CARDS.push(card)
        console.log(`Added file ${file.name}`)
        media.append(card.element.div)
    }
}

function createFileCard(file, parentUUid, number) {
    // Create new card that stores file upload progress
    return {
        uuid: "c43d3b1c-e726-4ed6-b8b9-03cb10841c1e",  // FIXME - make this dynamic
        parentUuid: parentUUid,
        file: file,
        element: new FileCardElement(file, number),
        number: number,
        previewIsVisible: false,

        send: function () {
            const xhr = new XMLHttpRequest()
            xhr.timeout = SEND_TIMEOUT

            xhr.upload.addEventListener('loadstart', (event) => {
                this.element.progress.value = 0
                this.element.progress.max = event.total
            });

            xhr.upload.addEventListener('progress', (event) => {
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

            function errorAction(event) {
                alert('Failed!')
                //{#progressBar.classList.remove("visible");#}
                //{#log.textContent = `Upload failed: ${event.type}`;#}
            }

            xhr.upload.addEventListener('error', errorAction);
            xhr.upload.addEventListener('abort', errorAction);
            xhr.upload.addEventListener('timeout', errorAction);

            const fileData = new FormData();
            fileData.append("file", file);

            xhr.open("PUT", `${ITEMS_ENDPOINT}/${this.uuid}/upload`, true);

            let features = getFeatures()
            for (const [key, value] of Object.entries(features)) {
                xhr.setRequestHeader(`X-Feature-${key.replaceAll('_', '-')}`, value)
            }
            xhr.setRequestHeader('X-Feature-Last-Modified', this.file.lastModifiedDate.toISOString())
            xhr.send(fileData);
            return xhr
        },
    }
}

class FileCardElement {
    // Helper object that displays file card
    constructor(file, number) {
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

        this.label = document.createElement("p")
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
        this.tagsLabel.append(this.tagsArea)
        this.right.append(this.tagsLabel)

        this.permissionsLabel = document.createElement("label")
        this.permissionsLabel.innerHTML = "Additional permissions for this item (one user per line):"
        this.permissionsArea = document.createElement("textarea")
        this.permissionsArea.rows = 5
        this.permissionsLabel.append(this.permissionsArea)
        this.right.append(this.permissionsLabel)

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
}

function uploadAllFiles() {
    // Perform uploading
    // TODO - get uuid for every item
    for (let card of CARDS) {
        card.send()
    }
    CARDS.length = 0
    document.getElementById(MEDIA_ID).replaceChildren()
    hideNavButtons()
    document.getElementById("upload-input").value = null;
    // TODO - move to uploaded items or stay here
}
