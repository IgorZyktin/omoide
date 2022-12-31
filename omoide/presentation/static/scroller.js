// half of a second
const SCROLLER_INTERVAL = 500

// pixels
const SCROLLER_HEIGHT = 100

// items to be loaded in one request
const DEFAULT_LOAD_AMOUNT = 10

// If we could not load anything in X attempts, do not continue
const GIVE_UP_AFTER_N_EMPTY_REQUESTS = 10

class Scroller {
    // Helper object that controls scrolling
    constructor(container, endpoint) {
        // Return new instance of a scroller object
        this.container = container
        this.endpoint = endpoint
        this.isActive = true
        this.nextUpload = new Date().getTime()
        this.lastSeen = -1
        this.alreadySeen = new Set()
        this.totalEmptyRequests = 0
        this.intervalId = null
    }

    trigger() {
        // Process uploading on every scroll
        if (!this.isActive) {
            return null
        }

        if (new Date().getTime() < this.nextUpload) {
            return null
        }

        let scrollY = window.scrollY
        let innerHeight = window.innerHeight
        let offsetHeight = document.body.offsetHeight
        let atTheBottom = scrollY + innerHeight > offsetHeight - SCROLLER_HEIGHT

        if (!atTheBottom) {
            return null
        }

        this.nextUpload = new Date().getTime() + SCROLLER_INTERVAL
        this.load()
    }

    stop() {
        // Turn dynamic load off
        this.isActive = false
        clearInterval(this.intervalId)
        let jump = document.createElement('a')
        jump.id = 'jump-to-top'
        jump.classList.add('to-top-link')
        jump.appendChild(document.createTextNode('Jump to top'));
        jump.title = 'Scroll back to top';
        jump.href = '#'
        jump.onclick = function () {
            jumpToTop(jump.id)
        }
        document.body.appendChild(jump);
    }

    inject(items, searchParams) {
        // Insert new items into page
        console.log(`Loading ${items.length} items`)

        let actuallyInjected = 0
        let last_item
        for (const item of items) {
            last_item = item

            this.lastSeen = Math.max(this.lastSeen, item['number'] || -1)

            if (this.alreadySeen.has(item['uuid'])) {
                continue
            } else {
                actuallyInjected += 1
            }

            this.alreadySeen.add(item['uuid'])

            let envelope = document.createElement('div')
            envelope.classList.add('envelope')
            if (item.is_collection) {
                envelope.classList.add('env-collection')
            }

            let link = document.createElement('a')
            searchParams.set('page', '1')
            link.href = item['href'] + '?' + searchParams.toString()
            link.title = item.parent_name ? item.parent_name : ''

            if (item.is_collection && item.name) {
                let name = document.createElement('p')
                name.innerText = item.name
                link.appendChild(name)
            }

            let img = document.createElement('img')
            img.src = item.thumbnail
            img.title = item.parent_name ? item.parent_name : ''
            link.appendChild(img)

            envelope.appendChild(link)
            this.container.appendChild(envelope);
        }

        if (actuallyInjected === 0) {
            this.totalEmptyRequests += 1
        } else {
            this.totalEmptyRequests = 0
        }

        if (this.totalEmptyRequests > GIVE_UP_AFTER_N_EMPTY_REQUESTS) {
            console.log(`Giving up on getting more items after ${this.totalEmptyRequests} attempts`)
            this.stop()
        }

        let expectedToLoad = Number.parseInt(searchParams.get('items_per_page'))
        if (items.length < (expectedToLoad || DEFAULT_LOAD_AMOUNT)) {
            console.log('Loaded everything from server')
            this.stop()
        }
    }

    load() {
        // Actually load new media
        let searchParams = new URLSearchParams(window.location.search)
        let self = this
        searchParams.set('items_per_page', searchParams.get('items_per_page') || DEFAULT_LOAD_AMOUNT)
        searchParams.set('last_seen', this.lastSeen)

        $.ajax({
            url: this.endpoint + '?' + searchParams.toString(),
            contentType: 'application/json',
        }).done(function (response) {
            self.inject(response, searchParams)
        }).fail(function (response) {
            let text = JSON.stringify(response)
            console.log(`Request to ${endpoint} returned response: ${text}`)
            self.stop()
        });
    }
}
