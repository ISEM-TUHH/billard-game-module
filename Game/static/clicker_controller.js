/*
Provides keyboard / presentation clicker navigation for collapsible sections
Works by adding clicker-index="x" to input elements (button, checkbox, radio-button) ascending, starting from 0, per collapsible section.
The index describes in which order inputs are selected.
*/

const ClickerController = {
    currentIndex: 0,
    isActive: false, // true when keyboard / presentation clicker is used
    activeSection: null,

    // listens for keypresses, deactivates if mouse or touch input is used
    init() {
        //window.reinitClicker = this.findActiveSection.bind(this);
        document.addEventListener('keydown', this.handleKeypress.bind(this));

        ['mousemove', 'touchstart', 'mousedown'].forEach(evt => {
            document.addEventListener(evt, () => this.clearFocus());
        });

        this.setupObserver();
        this.findActiveSection();
    },

    setupObserver() {
        const observer = new MutationObserver((mutations) => {
            clearTimeout(this.observerTimeout);
            this.observerTimeout = setTimeout(() => {
                this.findActiveSection();
            }, 50);
        });

        observer.observe(document.body, {
            attributes: true,
            childList: true,
            subtree: true,
            attributeFilter: ['style', 'class']
        });
    },

    findActiveSection() {
        const sections = Array.from(document.querySelectorAll('.collapsible-content'));
        const currentlyVisible = sections.find(sec => sec.style.display !== 'none');

        if (currentlyVisible && currentlyVisible !== this.activeSection) {
            this.activeSection = currentlyVisible;
            this.currentIndex = 0;
            //if (this.isActive) this.applyFocus();
        }

        if (this.isActive && this.activeSection) {
            const maxIndex = Math.max(0, this.getClickerElements().length - 1);
            this.currentIndex = Math.min(this.currentIndex, maxIndex);
            this.applyFocus();
        }
    },

    handleKeypress(e) {
        const nextKeys = ['PageDown', 'ArrowRight', 'ArrowDown'];
        const prevKeys = ['PageUp', 'ArrowLeft', 'ArrowUp'];
        const selectKeys = ['Enter', ' '];

        if (nextKeys.includes(e.key)) {
            e.preventDefault();
            this.navigate(1);
        } else if (prevKeys.includes(e.key)) {
            e.preventDefault();
            this.navigate(-1);
        } else if (selectKeys.includes(e.key) && this.isActive) {
            e.preventDefault();
            this.triggerClick();
        }
    },

    navigate(direction) {
        this.isActive = true;
        if (!this.activeSection) this.findActiveSection();
        if (!this.activeSection) return;

        const elements = this.getClickerElements();
        if (elements.length === 0) return;

        this.currentIndex = (this.currentIndex + direction + elements.length) % elements.length;
        this.applyFocus();
    },

    triggerClick() {
        if (!this.activeSection) return;
        //const target = this.activeSection.querySelector(`[clicker-index="${this.currentIndex}"]`);
        const target = this.getClickerElements()[this.currentIndex];
        if (target) {
            target.click();
        }
    },
    
    applyFocus() {
        document.querySelectorAll('.clicker-focused').forEach(el => {
            el.classList.remove('clicker-focused');
        });

        if (!this.activeSection) return;

        const target = this.getClickerElements()[this.currentIndex];
        // const target = this.activeSection.querySelector(`[clicker-index="${this.currentIndex}"]`);
        if (target) {
            target.classList.add('clicker-focused');
            target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    },

    clearFocus() {
        if (!this.isActive) return;
        this.isActive = false;
        document.querySelectorAll('.clicker-focused').forEach(el => {
            el.classList.remove('clicker-focused');
        });
    },

    getClickerElements() {
        if (!this.activeSection) return [];
        return Array.from(this.activeSection.querySelectorAll('[clicker-index]')).filter(el => !el.closest('.deactivated'));
    }
};

document.addEventListener('DOMContentLoaded', () => {
    ClickerController.init();
});