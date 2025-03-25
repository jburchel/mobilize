import { html } from 'lit-html';

export default {
  title: 'Design System/Tokens',
};

export const Colors = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Color Tokens</h1>
      
      <h2 style="margin-top: 2rem;">Brand Colors</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-primary-blue); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Primary Blue</div>
          <code style="font-size: 12px;">#183963</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-primary-blue-dark); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Primary Blue Dark</div>
          <code style="font-size: 12px;">#132E4C</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-primary-blue-light); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Primary Blue Light</div>
          <code style="font-size: 12px;">#2A5183</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-primary-green); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Primary Green</div>
          <code style="font-size: 12px;">#39A949</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-primary-green-dark); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Primary Green Dark</div>
          <code style="font-size: 12px;">#2E8A3C</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-primary-green-light); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Primary Green Light</div>
          <code style="font-size: 12px;">#4FBF5F</code>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Grayscale</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-100); border: 1px solid #ddd; border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 100</div>
          <code style="font-size: 12px;">var(--color-gray-100)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-200); border: 1px solid #ddd; border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 200</div>
          <code style="font-size: 12px;">var(--color-gray-200)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-300); border: 1px solid #ddd; border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 300</div>
          <code style="font-size: 12px;">var(--color-gray-300)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-400); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 400</div>
          <code style="font-size: 12px;">var(--color-gray-400)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-500); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 500</div>
          <code style="font-size: 12px;">var(--color-gray-500)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-600); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 600</div>
          <code style="font-size: 12px;">var(--color-gray-600)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-700); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 700</div>
          <code style="font-size: 12px;">var(--color-gray-700)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-800); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 800</div>
          <code style="font-size: 12px;">var(--color-gray-800)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-gray-900); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Gray 900</div>
          <code style="font-size: 12px;">var(--color-gray-900)</code>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Feedback Colors</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem;">
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-success); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Success</div>
          <code style="font-size: 12px;">var(--color-success)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-info); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Info</div>
          <code style="font-size: 12px;">var(--color-info)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-warning); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Warning</div>
          <code style="font-size: 12px;">var(--color-warning)</code>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center;">
          <div style="width: 100px; height: 100px; background-color: var(--color-danger); border-radius: 8px;"></div>
          <div style="margin-top: 0.5rem;">Danger</div>
          <code style="font-size: 12px;">var(--color-danger)</code>
        </div>
      </div>
    </div>
  `;
};

export const Typography = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Typography Tokens</h1>
      
      <h2 style="margin-top: 2rem;">Font Families</h2>
      <div style="margin-bottom: 2rem;">
        <div style="margin-bottom: 1rem;">
          <div style="font-weight: var(--font-weight-bold);">Heading Font</div>
          <div style="font-family: var(--font-family-headings); font-size: 1.5rem;">The quick brown fox jumps over the lazy dog</div>
          <code style="font-size: 12px;">var(--font-family-headings)</code>
        </div>
        <div>
          <div style="font-weight: var(--font-weight-bold);">Base Font</div>
          <div style="font-family: var(--font-family-base); font-size: 1rem;">The quick brown fox jumps over the lazy dog</div>
          <code style="font-size: 12px;">var(--font-family-base)</code>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Font Sizes</h2>
      <div style="margin-bottom: 2rem;">
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <div style="font-size: var(--font-size-4xl);">Heading 1</div>
            <code style="font-size: 12px;">var(--font-size-4xl)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-3xl);">Heading 2</div>
            <code style="font-size: 12px;">var(--font-size-3xl)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-2xl);">Heading 3</div>
            <code style="font-size: 12px;">var(--font-size-2xl)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-xl);">Heading 4</div>
            <code style="font-size: 12px;">var(--font-size-xl)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-lg);">Heading 5</div>
            <code style="font-size: 12px;">var(--font-size-lg)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-md);">Base Text</div>
            <code style="font-size: 12px;">var(--font-size-md)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-sm);">Small Text</div>
            <code style="font-size: 12px;">var(--font-size-sm)</code>
          </div>
          <div>
            <div style="font-size: var(--font-size-xs);">Extra Small Text</div>
            <code style="font-size: 12px;">var(--font-size-xs)</code>
          </div>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Font Weights</h2>
      <div style="margin-bottom: 2rem;">
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <div style="font-weight: var(--font-weight-light);">Light (300)</div>
            <code style="font-size: 12px;">var(--font-weight-light)</code>
          </div>
          <div>
            <div style="font-weight: var(--font-weight-normal);">Normal (400)</div>
            <code style="font-size: 12px;">var(--font-weight-normal)</code>
          </div>
          <div>
            <div style="font-weight: var(--font-weight-medium);">Medium (500)</div>
            <code style="font-size: 12px;">var(--font-weight-medium)</code>
          </div>
          <div>
            <div style="font-weight: var(--font-weight-semibold);">Semibold (600)</div>
            <code style="font-size: 12px;">var(--font-weight-semibold)</code>
          </div>
          <div>
            <div style="font-weight: var(--font-weight-bold);">Bold (700)</div>
            <code style="font-size: 12px;">var(--font-weight-bold)</code>
          </div>
        </div>
      </div>
    </div>
  `;
};

export const Spacing = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Spacing Tokens</h1>
      
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-2xs); height: var(--spacing-2xs); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>2XS (4px) - var(--spacing-2xs)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-xs); height: var(--spacing-xs); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>XS (8px) - var(--spacing-xs)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-sm); height: var(--spacing-sm); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>SM (12px) - var(--spacing-sm)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-md); height: var(--spacing-md); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>MD (16px) - var(--spacing-md)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-lg); height: var(--spacing-lg); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>LG (24px) - var(--spacing-lg)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-xl); height: var(--spacing-xl); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>XL (32px) - var(--spacing-xl)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-2xl); height: var(--spacing-2xl); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>2XL (48px) - var(--spacing-2xl)</div>
        </div>
        <div style="display: flex; align-items: center;">
          <div style="width: var(--spacing-3xl); height: var(--spacing-3xl); background-color: var(--color-primary-blue); margin-right: 1rem;"></div>
          <div>3XL (64px) - var(--spacing-3xl)</div>
        </div>
      </div>
    </div>
  `;
}; 