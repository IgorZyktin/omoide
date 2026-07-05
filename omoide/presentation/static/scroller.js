// half of a second
const SCROLLER_INTERVAL = 500;

// pixels
const SCROLLER_HEIGHT = 1000;

// items to be loaded in one request
const DEFAULT_LOAD_AMOUNT = 10;

// If we could not load anything in X attempts, do not continue
const GIVE_UP_AFTER_N_EMPTY_REQUESTS = 10;

class Scroller {
    /**
     * Creates a new Scroller instance
     * @param {HTMLElement} container - The container to append items to
     * @param {string} endpoint - The API endpoint to fetch data from
     */
    constructor(container, endpoint) {
        this.container = container;
        this.endpoint = endpoint;
        this.isActive = true;
        this.nextUpload = Date.now();
        this.lastSeen = -1;
        this.alreadySeen = new Set();
        this.totalEmptyRequests = 0;
        this.intervalId = null;
        this.tryNotOnlyCollections = false;
        this.isProcessing = false;
    }

    /**
     * Trigger scroll handling
     */
    trigger() {
        if (!this.isActive || this.isProcessing) {
            return;
        }

        if (Date.now() < this.nextUpload) {
            return;
        }

        const scrollY = window.scrollY;
        const innerHeight = window.innerHeight;
        const offsetHeight = document.body.offsetHeight;
        const atTheBottom = scrollY + innerHeight > offsetHeight - SCROLLER_HEIGHT;

        if (!atTheBottom) {
            return;
        }

        this.nextUpload = Date.now() + SCROLLER_INTERVAL;
        this.load();
    }

    /**
     * Stop the scroller and add jump-to-top link
     */
    stop() {
        this.isActive = false;
        clearInterval(this.intervalId);

        // Create jump-to-top link
        const jump = document.createElement('a');
        jump.id = 'jump-to-top';
        jump.className = 'to-top-link';
        jump.textContent = 'Jump to top';
        jump.title = 'Scroll back to top';
        jump.href = '#';
        jump.onclick = (e) => {
            e.preventDefault();
            this.jumpToTop();
        };

        document.body.appendChild(jump);
    }

    /**
     * Jump to top of page
     */
    jumpToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    /**
     * Insert new items into page
     * @param {Object} response - API response containing items
     * @param {URLSearchParams} searchParams - Current search parameters
     */
    inject(response, searchParams) {
        const items = response.items || response;

        // Handle collections toggle
        let switchedMode = false;
        if (items.length === 0 && !this.tryNotOnlyCollections && searchParams.get('collections') === 'on') {
            switchedMode = true;
            this.tryNotOnlyCollections = true;
            console.log('Seems that user got no results because "only collections" is active');
        }

        console.log(`Loading ${items.length} items`);

        let actuallyInjected = 0;
        let lastItem = null;

        for (const item of items) {
            lastItem = item;
            this.lastSeen = item.number;

            if (this.alreadySeen.has(item.uuid)) {
                continue;
            }

            actuallyInjected += 1;
            this.alreadySeen.add(item.uuid);

            const envelope = this.createEnvelope(item, searchParams);
            this.container.appendChild(envelope);
        }

        // Update empty request counter
        if (actuallyInjected === 0) {
            this.totalEmptyRequests += 1;
        } else {
            this.totalEmptyRequests = 0;
        }

        // Check if we should give up
        if (this.totalEmptyRequests > GIVE_UP_AFTER_N_EMPTY_REQUESTS) {
            console.log(`Giving up on getting more items after ${this.totalEmptyRequests} attempts`);
            this.stop();
            return;
        }

        // Check if we've loaded everything
        const expectedToLoad = Number.parseInt(searchParams.get('items_per_page')) || DEFAULT_LOAD_AMOUNT;
        if (items.length < expectedToLoad && !switchedMode) {
            console.log('Loaded everything from server');
            this.stop();
        }
    }

    /**
     * Create envelope element for an item
     * @param {Object} item - The item data
     * @param {URLSearchParams} searchParams - Search parameters
     * @returns {HTMLElement} The created envelope element
     */
    createEnvelope(item, searchParams) {
        const envelope = document.createElement('div');
        envelope.className = 'envelope';

        if (item.is_collection) {
            envelope.classList.add('env-collection');
        }

        const link = document.createElement('a');
        searchParams.set('page', '1');
        link.href = getPreviewUrl(item);

        // Handle parent name
        let parentName = '';
        if (item.extras !== undefined && item.extras.parent_name) {
            parentName = item.extras.parent_name;
        }
        link.title = parentName;

        // Handle item display based on type
        if (item.is_collection && item.name) {
            const name = document.createElement('p');
            name.textContent = item.name;
            link.appendChild(name);
        } else if (!item.is_collection && itemIsVideo(item)) {
            if (item.name) {
                const label = document.createElement('span');
                label.className = 'envelope-video-title';
                label.textContent = item.name;
                link.appendChild(label);
            }

            const sign = document.createElement('div');
            sign.className = 'triangle-overlay';
            link.appendChild(sign);
        }

        // Create image element
        const img = document.createElement('img');
        img.src = getThumbnailContentUrl(item);
        img.title = parentName;
        img.width = item.extras.thumbnail_width;
        img.height = item.extras.thumbnail_height;
        img.addEventListener('load', updateImageSize);
        link.appendChild(img);

        envelope.appendChild(link);
        return envelope;
    }

    /**
     * Load new media items
     */
    async load() {
        if (this.isProcessing) return;

        this.isProcessing = true;

        try {
            const searchParams = new URLSearchParams(window.location.search);
            searchParams.set('items_per_page', searchParams.get('items_per_page') || DEFAULT_LOAD_AMOUNT);
            searchParams.set('last_seen', this.lastSeen);

            if (this.tryNotOnlyCollections) {
                searchParams.set('collections', 'off');
            }

            const response = await fetch(`${this.endpoint}?${searchParams.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.inject(data, searchParams);
        } catch (error) {
            console.error(`Request to ${this.endpoint} failed:`, error);
            this.stop();
        } finally {
            this.isProcessing = false;
        }
    }
}
