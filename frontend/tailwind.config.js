/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        woye: '#3D3028',
        baiyan: '#EAE4DA',
      },
      fontFamily: {
        'brand-zh': ['"方正FW筑紫明朝"', 'serif'],
        'system-zh': ['"Noto Sans CJK SC"', 'sans-serif'],
        'system-en': ['"DIN Pro"', 'sans-serif'],
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: false,
  },
}
