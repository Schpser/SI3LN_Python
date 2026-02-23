// mobile.js - Mobile and touch-specific functionality
class MobileManager {
    constructor() {
        this.isMobile = this.detectMobile();
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.swipeThreshold = 50; // Minimum distance for swipe
    }

    detectMobile() {
        // Check if device is mobile/tablet
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    init() {
        if (this.isMobile) {
            this.addMobileClass();
            this.initTouchHandlers();
            this.initViewportMeta();
            this.preventDefaultBehaviors();
            this.initPullToRefresh();
            console.log('Mobile mode activated');
        }
    }

    addMobileClass() {
        document.body.classList.add('mobile-device');
    }

    initViewportMeta() {
        // Ensure viewport meta tag is optimal for mobile
        let viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 
                'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes, viewport-fit=cover'
            );
        }
    }

    initTouchHandlers() {
        // Swipe gestures
        document.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
            this.touchStartY = e.changedTouches[0].screenY;
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.touchEndY = e.changedTouches[0].screenY;
            this.handleSwipe();
        }, { passive: true });

        // Double tap to close menu
        this.initDoubleTap();

        // Long press handlers
        this.initLongPress();

        // Touch feedback
        this.addTouchFeedback();
    }

    handleSwipe() {
        const diffX = this.touchEndX - this.touchStartX;
        const diffY = this.touchEndY - this.touchStartY;
        const absDiffX = Math.abs(diffX);
        const absDiffY = Math.abs(diffY);

        // Ignore if not a swipe (too small movement)
        if (absDiffX < this.swipeThreshold && absDiffY < this.swipeThreshold) {
            return;
        }

        // Horizontal swipe is more significant
        if (absDiffX > absDiffY) {
            if (diffX > 0) {
                this.onSwipeRight();
            } else {
                this.onSwipeLeft();
            }
        } else {
            // Vertical swipe
            if (diffY > 0) {
                this.onSwipeDown();
            } else {
                this.onSwipeUp();
            }
        }
    }

    onSwipeRight() {
        // Swipe right: Open menu
        const menu = document.querySelector('.menu-dropdown');
        if (menu && !menu.classList.contains('visible')) {
            menu.classList.add('visible');
        }
    }

    onSwipeLeft() {
        // Swipe left: Close menu
        const menu = document.querySelector('.menu-dropdown');
        if (menu && menu.classList.contains('visible')) {
            menu.classList.remove('visible');
        }
    }

    onSwipeUp() {
        // Swipe up: Could be used for navigation
        // Currently not implementing to avoid conflicts
    }

    onSwipeDown() {
        // Swipe down: Could be used for refresh
        // Handled by pull-to-refresh
    }

    initDoubleTap() {
        let lastTap = 0;
        document.addEventListener('touchend', (e) => {
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;
            
            if (tapLength < 300 && tapLength > 0) {
                // Double tap detected
                this.onDoubleTap(e);
            }
            lastTap = currentTime;
        });
    }

    onDoubleTap(e) {
        // Double tap on menu area to close
        const menu = document.querySelector('.menu-dropdown');
        if (menu && menu.contains(e.target)) {
            menu.classList.remove('visible');
        }
    }

    initLongPress() {
        let pressTimer;
        
        document.querySelectorAll('.game-card, .help-card, .card').forEach(card => {
            card.addEventListener('touchstart', (e) => {
                pressTimer = setTimeout(() => {
                    this.onLongPress(card, e);
                }, 500);
            });

            card.addEventListener('touchend', () => {
                clearTimeout(pressTimer);
            });

            card.addEventListener('touchmove', () => {
                clearTimeout(pressTimer);
            });
        });
    }

    onLongPress(element, e) {
        // Add haptic feedback if available
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }

        // Could show context menu or additional options
        console.log('Long press detected on:', element);
    }

    addTouchFeedback() {
        // Add visual feedback for touch interactions
        const touchableElements = document.querySelectorAll(
            'button, .menu-item, .card, .help-btn, .game-control-btn, .game-nav-btn, a'
        );

        touchableElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            });

            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('touch-active');
                }, 150);
            });

            element.addEventListener('touchcancel', function() {
                this.classList.remove('touch-active');
            });
        });
    }

    preventDefaultBehaviors() {
        // Prevent default behaviors that interfere with mobile UX
        
        // Prevent double-tap zoom on buttons
        document.querySelectorAll('button, .menu-item, .help-btn').forEach(element => {
            element.addEventListener('touchend', (e) => {
                e.preventDefault();
                e.target.click();
            });
        });

        // Prevent pull-to-refresh on game page
        const gamePlayPage = document.getElementById('game-play-page');
        if (gamePlayPage) {
            gamePlayPage.addEventListener('touchmove', (e) => {
                if (window.scrollY === 0) {
                    e.preventDefault();
                }
            }, { passive: false });
        }
    }

    initPullToRefresh() {
        let startY = 0;
        let pullDistance = 0;
        const threshold = 80;

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (window.scrollY === 0) {
                pullDistance = e.touches[0].clientY - startY;
                
                if (pullDistance > 0 && pullDistance < threshold) {
                    // Show pull indicator (you can add visual feedback here)
                }
            }
        }, { passive: true });

        document.addEventListener('touchend', () => {
            if (pullDistance > threshold) {
                // Trigger refresh
                this.refreshContent();
            }
            pullDistance = 0;
        });
    }

    refreshContent() {
        // Reload current page data
        if (window.app) {
            const currentPage = document.querySelector('.page:not(.hidden)');
            if (currentPage && currentPage.id) {
                const pageName = currentPage.id.replace('-page', '');
                console.log('Refreshing page:', pageName);
                
                // Add visual feedback
                if (navigator.vibrate) {
                    navigator.vibrate(30);
                }
                
                // Reload page data
                window.app.loadPageData(pageName);
            }
        }
    }

    // Touch-optimized navigation for games
    initGameTouchControls() {
        const gameFrame = document.getElementById('gameFrame');
        if (!gameFrame) return;

        // Add touch event listeners to game frame
        gameFrame.addEventListener('touchstart', (e) => {
            // Handle game-specific touch events
            // This will be passed to the game iframe
        }, { passive: false });
    }

    // Orientation change handling
    initOrientationHandler() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                // Recalculate layout after orientation change
                this.adjustLayoutForOrientation();
            }, 100);
        });
    }

    adjustLayoutForOrientation() {
        const orientation = window.orientation;
        
        if (orientation === 90 || orientation === -90) {
            // Landscape
            document.body.classList.add('landscape');
            document.body.classList.remove('portrait');
        } else {
            // Portrait
            document.body.classList.add('portrait');
            document.body.classList.remove('landscape');
        }
    }

    // Enable fullscreen on mobile
    enableMobileFullscreen() {
        const gamePlayPage = document.getElementById('game-play-page');
        if (gamePlayPage && !gamePlayPage.classList.contains('hidden')) {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            } else if (document.documentElement.webkitRequestFullscreen) {
                document.documentElement.webkitRequestFullscreen();
            }
        }
    }

    // Haptic feedback helper
    hapticFeedback(pattern = 50) {
        if (navigator.vibrate) {
            navigator.vibrate(pattern);
        }
    }

    // Check if device supports touch
    hasTouch() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    // Get device info
    getDeviceInfo() {
        return {
            isMobile: this.isMobile,
            hasTouch: this.hasTouch(),
            screenWidth: window.innerWidth,
            screenHeight: window.innerHeight,
            orientation: window.orientation || 0,
            devicePixelRatio: window.devicePixelRatio || 1
        };
    }
}

// Export for use in main app
window.MobileManager = MobileManager;
