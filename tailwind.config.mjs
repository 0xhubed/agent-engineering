/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        newsprint: {
          50: '#f9f6f0',
          100: '#f0ead8',
          200: '#e0d4b4',
          300: '#c8b98a',
          400: '#b09d6a',
          500: '#8c7d52',
          600: '#6e6140',
          700: '#574c32',
          800: '#3e3522',
          900: '#281f0e',
        },
        ink: {
          DEFAULT: '#1a1209',
          light: '#3d2e14',
          muted: '#6b5c3e',
          faint: '#9e8d6f',
        },
      },
      fontFamily: {
        serif: ['EB Garamond', 'Georgia', 'serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': theme('colors.ink.light'),
            '--tw-prose-headings': theme('colors.ink.DEFAULT'),
            '--tw-prose-links': theme('colors.ink.light'),
            '--tw-prose-bold': theme('colors.ink.DEFAULT'),
            '--tw-prose-counters': theme('colors.ink.muted'),
            '--tw-prose-bullets': theme('colors.ink.muted'),
            '--tw-prose-hr': theme('colors.newsprint.200'),
            '--tw-prose-quotes': theme('colors.ink.DEFAULT'),
            '--tw-prose-quote-borders': theme('colors.newsprint.400'),
            '--tw-prose-captions': theme('colors.ink.muted'),
            '--tw-prose-code': theme('colors.ink.DEFAULT'),
            '--tw-prose-pre-code': theme('colors.ink.light'),
            '--tw-prose-pre-bg': theme('colors.newsprint.100'),
            '--tw-prose-th-borders': theme('colors.newsprint.300'),
            '--tw-prose-td-borders': theme('colors.newsprint.200'),
            fontFamily: theme('fontFamily.serif').join(', '),
            fontSize: '1.0625rem',
            lineHeight: '1.75',
            code: {
              backgroundColor: theme('colors.newsprint.100'),
              padding: '0.15rem 0.35rem',
              borderRadius: '0.2rem',
              fontWeight: '400',
              fontFamily: theme('fontFamily.mono').join(', '),
            },
            'code::before': { content: '""' },
            'code::after': { content: '""' },
          },
        },
      }),
    },
  },
  plugins: [
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('@tailwindcss/typography'),
  ],
};
