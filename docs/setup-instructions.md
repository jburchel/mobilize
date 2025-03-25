# Design System Setup Instructions

This document provides step-by-step instructions for setting up and implementing the design system incrementally.

## Step 1: Design Tokens Integration (Current State)

We've created a design tokens CSS file located at `app/static/css/design-tokens.css`. This file contains all the CSS variables that define our design system's foundations:

- Color palette
- Typography scale
- Spacing system
- Borders, shadows, and transitions

### How to Test This Step

1. The design tokens file is already linked in the base.html template
2. Run the Flask application to check that the site loads correctly:
   ```bash
   flask run
   ```
3. Verify that no styles are broken by the addition of the design tokens file

## Step 2: Applying Design Tokens to Existing Styles (Next Step)

Once we confirm the design tokens are working properly, we can begin refactoring the existing CSS to use these tokens:

1. Identify a small section of the application to update first (e.g., buttons or form fields)
2. Update the CSS for that section to use design tokens instead of hardcoded values
3. Test to ensure everything still looks correct

### Example of Token Application

```css
/* Before */
.btn-primary {
    background-color: #183963;
    border-color: #183963;
}

/* After */
.btn-primary {
    background-color: var(--color-primary-blue);
    border-color: var(--color-primary-blue);
}
```

## Step 3: Build Process Setup (Future Task)

Once we've successfully applied design tokens to a few components, we can set up the build process:

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Create necessary directories:
   ```bash
   mkdir -p app/static/css/dist
   mkdir -p stories
   mkdir -p .storybook
   ```

3. Run a simplified build process:
   ```bash
   npx postcss app/static/css/design-tokens.css -o app/static/css/dist/design-tokens.css
   ```

## Step 4: Component Documentation (Future Task)

Once the build process is working, we can set up Storybook for component documentation.

## Troubleshooting

If you encounter any issues:

1. Check the browser console for CSS errors
2. Verify that all CSS files are being loaded correctly
3. Ensure path references in HTML templates match the actual file locations
4. For build process issues, check Node.js and npm versions 