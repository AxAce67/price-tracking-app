document.addEventListener('DOMContentLoaded', (event) => {
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');
    const progressBar = document.getElementById('progress-bar');
    const container = document.querySelector('.container');

    let loadingComplete = false;

    // ローディングアニメーションを表示する関数
    window.showLoading = function(message = 'Loading...', progressUrl = '/progress') {
        loadingComplete = false;
        loadingText.textContent = message + ' 0%';
        loading.style.display = 'flex';
        container.style.display = 'none';
        startProgressStream(progressUrl);
    };

    // ローディングアニメーションを非表示にする関数
    window.hideLoading = function() {
        loading.style.display = 'none';
        container.style.display = 'block';
    };

    // SSEを使用してプログレスを更新する関数
    function startProgressStream(progressUrl) {
        const eventSource = new EventSource(progressUrl);
        let currentProgress = 0;

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (currentProgress < 100) {
                animateProgress(currentProgress, data.progress, data.step);
                currentProgress = data.progress;
            }

            if (data.progress >= 100) {
                eventSource.close();
                if (loadingComplete) {
                    hideLoading();
                }
            }
        };

        eventSource.onerror = function() {
            eventSource.close();
            if (loadingComplete) {
                hideLoading();
            }
        };
    }

    // プログレスバーをアニメーションさせる関数
    function animateProgress(start, end, step) {
        const duration = 200;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            const currentProgress = start + (end - start) * progress;

            progressBar.style.width = `${currentProgress}%`;
            loadingText.textContent = `${step}... ${Math.round(currentProgress)}%`;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    // ページの読み込みが完了したらローディングを非表示にし、コンテンツを表示
    window.addEventListener('load', () => {
        loadingComplete = true;
        if (progressBar.style.width === '100%') {
            hideLoading();
        }
        
        // 結果ページの場合のみヘッダーとセクションのアニメーションを適用
        if (document.querySelector('.result-section')) {
            // ヘッダーのアニメーション
            anime({
                targets: 'header',
                translateY: [-50, 0],
                opacity: [0, 1],
                duration: 800,
                easing: 'easeOutElastic(1, .8)',
                delay: 300
            });

            // セクションのアニメーション
            anime({
                targets: '.result-section',
                translateY: [50, 0],
                opacity: [0, 1],
                duration: 800,
                delay: anime.stagger(200, {start: 500}),
                easing: 'easeOutCubic'
            });
        }
    });

    // ボタンのアニメーション関数
    window.animateButton = function(button) {
        button.addEventListener('click', function(e) {
            const form = this.closest('form');
            if (form && form.id === 'notification-form') {
                e.preventDefault();
                const targetPrice = form.querySelector('#target_price');
                const email = form.querySelector('#email');
                const errorMessage = form.querySelector('#notification-error');
                
                if (!targetPrice.value.trim() && !email.value.trim()) {
                    errorMessage.textContent = '目標価格とメールアドレスを入力してください';
                    errorMessage.style.display = 'block';
                    return;
                } else if (!targetPrice.value.trim()) {
                    errorMessage.textContent = '目標価格を入力してください';
                    errorMessage.style.display = 'block';
                    return;
                } else if (!email.value.trim()) {
                    errorMessage.textContent = 'メールアドレスを入力してください';
                    errorMessage.style.display = 'block';
                    return;
                }
                
                errorMessage.style.display = 'none';
                
                anime({
                    targets: this,
                    scale: [1, 0.95, 1],
                    duration: 300,
                    easing: 'easeInOutQuad',
                    complete: () => {
                        showLoading(this.dataset.loadingMessage || 'Loading...', '/email_notification_progress');
                        setTimeout(() => {
                            form.submit();
                        }, 500);
                    }
                });
            } else if (form && form.id === 'tracking-form') {
                // 追跡開始ボタンのクリック処理は form の submit イベントで行うため、ここでは何もしない
                return;
            } else if (this.classList.contains('btn-primary') && this.tagName.toLowerCase() === 'a') {
                // 商品ページに戻るボタンの場合、アニメーションとローディングを適用しない
                return;
            }
        });

        // ホバーエフェクトのアニメーション
        button.addEventListener('mouseenter', () => {
            anime({
                targets: button,
                backgroundColor: '#0056b3',
                scale: 1.05,
                duration: 300,
                easing: 'easeOutQuad'
            });
        });

        button.addEventListener('mouseleave', () => {
            anime({
                targets: button,
                backgroundColor: '#bf0000',
                scale: 1,
                duration: 300,
                easing: 'easeOutQuad'
            });
        });
    };

    // すべてのボタンにアニメーションを適用
    document.querySelectorAll('.btn').forEach(animateButton);

    // メール送信完了ページのアニメーション
    window.animateEmailSentPage = function() {
        // ヘッダーのアニメーション
        anime({
            targets: 'header',
            translateY: [-50, 0],
            opacity: [0, 1],
            duration: 1000,
            easing: 'easeOutElastic(1, .8)',
            delay: 300
        });

        // セクションのアニメーション
        anime({
            targets: '.result-section',
            translateY: [50, 0],
            opacity: [0, 1],
            duration: 800,
            easing: 'easeOutCubic',
            delay: 500
        });

        // リストアイテムのアニメーション
        anime({
            targets: '.result-section ul li',
            translateX: [-50, 0],
            opacity: [0, 1],
            duration: 600,
            easing: 'easeOutQuad',
            delay: anime.stagger(100, {start: 800})
        });

        // ハイライト要素のアニメーション
        anime({
            targets: '.highlight',
            backgroundColor: ['rgba(255,255,255,0)', 'rgba(255,215,0,0.3)', 'rgba(255,255,255,0)'],
            duration: 1500,
            easing: 'easeInOutQuad',
            delay: anime.stagger(200, {start: 1200})
        });
    };

    // ページ読み込み時にアニメーションを実行
    if (document.querySelector('.result-section')) {
        if (document.body.classList.contains('email-sent-page')) {
            animateEmailSentPage();
        } else {
            // 結果ページのアニメーション（既存のコード）
            // ヘッダーのアニメーション
            anime({
                targets: 'header',
                translateY: [-50, 0],
                opacity: [0, 1],
                duration: 800,
                easing: 'easeOutElastic(1, .8)',
                delay: 300
            });

            // セクションのアニメーション
            anime({
                targets: '.result-section',
                translateY: [50, 0],
                opacity: [0, 1],
                duration: 800,
                delay: anime.stagger(200, {start: 500}),
                easing: 'easeOutCubic'
            });
        }
    }
});
