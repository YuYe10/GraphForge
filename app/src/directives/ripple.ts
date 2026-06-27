/**
 * Ripple Effect Directive
 * Material Design 风格的水波纹点击反馈
 *
 * Usage: v-ripple or v-ripple.light
 */
import type { Directive } from 'vue'

interface RippleElement extends HTMLElement {
  _rippleHandler?: (e: MouseEvent) => void
}

function createRipple(event: MouseEvent, el: RippleElement, light = false) {
  const rect = el.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height) * 2
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2

  const ripple = document.createElement('span')
  ripple.className = 'v-ripple-inner'
  ripple.style.cssText = `
    position: absolute;
    border-radius: 50%;
    width: ${size}px;
    height: ${size}px;
    left: ${x}px;
    top: ${y}px;
    pointer-events: none;
    background: ${light ? 'rgba(255,255,255,0.4)' : 'rgba(194,164,116,0.3)'};
    animation: ripple-effect 0.7s ease-out forwards;
    z-index: 0;
  `

  el.style.position = el.style.position || 'relative'
  el.style.overflow = el.style.overflow || 'hidden'
  el.appendChild(ripple)

  ripple.addEventListener('animationend', () => {
    ripple.remove()
  })
}

export const vRipple: Directive<RippleElement> = {
  mounted(el: RippleElement, binding) {
    const light = binding.arg === 'light' || binding.modifiers?.light
    const handler = (e: MouseEvent) => createRipple(e, el, light)
    el._rippleHandler = handler
    el.addEventListener('click', handler)
    el.style.cursor = 'pointer'
  },
  unmounted(el: RippleElement) {
    if (el._rippleHandler) {
      el.removeEventListener('click', el._rippleHandler)
    }
  },
}
