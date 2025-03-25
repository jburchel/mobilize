import { html } from 'lit-html';

export default {
  title: 'Components/Form Elements',
};

export const TextInputs = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/form-elements.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Text Inputs</h2>
    
    <div style="margin-bottom: 24px;">
      <label for="standard-input" class="form-label">Standard Input</label>
      <input type="text" id="standard-input" class="form-control" placeholder="Enter text">
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-help" class="form-label">Input with Help Text</label>
      <input type="text" id="input-with-help" class="form-control" placeholder="Enter your email">
      <div class="form-text">We'll never share your email with anyone else.</div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="disabled-input" class="form-label">Disabled Input</label>
      <input type="text" id="disabled-input" class="form-control" placeholder="This field is disabled" disabled>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="readonly-input" class="form-label">Readonly Input</label>
      <input type="text" id="readonly-input" class="form-control" value="This value cannot be changed" readonly>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="required-input" class="form-label required">Required Input</label>
      <input type="text" id="required-input" class="form-control" placeholder="This field is required" required>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="valid-input" class="form-label">Valid Input</label>
      <input type="text" id="valid-input" class="form-control is-valid" value="Correct value">
      <div class="valid-feedback">Looks good!</div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="invalid-input" class="form-label">Invalid Input</label>
      <input type="text" id="invalid-input" class="form-control is-invalid" value="Incorrect value">
      <div class="invalid-feedback">Please provide a valid value.</div>
    </div>
  </div>
`;

export const SelectInputs = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/form-elements.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Select Inputs</h2>
    
    <div style="margin-bottom: 24px;">
      <label for="standard-select" class="form-label">Standard Select</label>
      <select id="standard-select" class="form-select">
        <option selected>Choose an option</option>
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
        <option value="3">Option 3</option>
      </select>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="disabled-select" class="form-label">Disabled Select</label>
      <select id="disabled-select" class="form-select" disabled>
        <option selected>This select is disabled</option>
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
        <option value="3">Option 3</option>
      </select>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="multiple-select" class="form-label">Multiple Select</label>
      <select id="multiple-select" class="form-select" multiple>
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
        <option value="3">Option 3</option>
        <option value="4">Option 4</option>
        <option value="5">Option 5</option>
      </select>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="valid-select" class="form-label">Valid Select</label>
      <select id="valid-select" class="form-select is-valid">
        <option>Choose an option</option>
        <option value="1" selected>Option 1</option>
        <option value="2">Option 2</option>
        <option value="3">Option 3</option>
      </select>
      <div class="valid-feedback">Looks good!</div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="invalid-select" class="form-label">Invalid Select</label>
      <select id="invalid-select" class="form-select is-invalid">
        <option selected>Choose an option</option>
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
        <option value="3">Option 3</option>
      </select>
      <div class="invalid-feedback">Please select an option.</div>
    </div>
  </div>
`;

export const CheckboxesAndRadios = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/form-elements.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Checkboxes and Radios</h2>
    
    <h3 style="margin-top: 24px;">Checkboxes</h3>
    <div style="margin-top: 12px;">
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="checkbox1">
        <label class="form-check-label" for="checkbox1">
          Default checkbox
        </label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="checkbox2" checked>
        <label class="form-check-label" for="checkbox2">
          Checked checkbox
        </label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="checkbox3" disabled>
        <label class="form-check-label" for="checkbox3">
          Disabled checkbox
        </label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="checkbox4" checked disabled>
        <label class="form-check-label" for="checkbox4">
          Disabled checked checkbox
        </label>
      </div>
    </div>
    
    <h3 style="margin-top: 24px;">Radio Buttons</h3>
    <div style="margin-top: 12px;">
      <div class="form-check">
        <input class="form-check-input" type="radio" name="radioGroup1" id="radio1" checked>
        <label class="form-check-label" for="radio1">
          Default radio
        </label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="radioGroup1" id="radio2">
        <label class="form-check-label" for="radio2">
          Second default radio
        </label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="radioGroup2" id="radio3" disabled>
        <label class="form-check-label" for="radio3">
          Disabled radio
        </label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="radioGroup2" id="radio4" checked disabled>
        <label class="form-check-label" for="radio4">
          Disabled checked radio
        </label>
      </div>
    </div>
    
    <h3 style="margin-top: 24px;">Switch Checkboxes</h3>
    <div style="margin-top: 12px;">
      <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="switch1">
        <label class="form-check-label" for="switch1">
          Default switch
        </label>
      </div>
      <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="switch2" checked>
        <label class="form-check-label" for="switch2">
          Checked switch
        </label>
      </div>
      <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="switch3" disabled>
        <label class="form-check-label" for="switch3">
          Disabled switch
        </label>
      </div>
      <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="switch4" checked disabled>
        <label class="form-check-label" for="switch4">
          Disabled checked switch
        </label>
      </div>
    </div>
  </div>
`;

export const TextAreas = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/form-elements.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Text Areas</h2>
    
    <div style="margin-bottom: 24px;">
      <label for="standard-textarea" class="form-label">Standard Textarea</label>
      <textarea id="standard-textarea" class="form-control" rows="3" placeholder="Enter your message here"></textarea>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="textarea-with-help" class="form-label">Textarea with Help Text</label>
      <textarea id="textarea-with-help" class="form-control" rows="3" placeholder="Enter your feedback"></textarea>
      <div class="form-text">Your feedback helps us improve our service.</div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="disabled-textarea" class="form-label">Disabled Textarea</label>
      <textarea id="disabled-textarea" class="form-control" rows="3" placeholder="This textarea is disabled" disabled></textarea>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="readonly-textarea" class="form-label">Readonly Textarea</label>
      <textarea id="readonly-textarea" class="form-control" rows="3" readonly>This content cannot be modified by the user.</textarea>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="valid-textarea" class="form-label">Valid Textarea</label>
      <textarea id="valid-textarea" class="form-control is-valid" rows="3">This is a valid message.</textarea>
      <div class="valid-feedback">Your message looks good!</div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="invalid-textarea" class="form-label">Invalid Textarea</label>
      <textarea id="invalid-textarea" class="form-control is-invalid" rows="3">Th</textarea>
      <div class="invalid-feedback">Please enter at least 10 characters.</div>
    </div>
  </div>
`;

export const InputGroups = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/form-elements.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Input Groups</h2>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-text" class="form-label">Input with Text Addon</label>
      <div class="input-group">
        <span class="input-group-text">@</span>
        <input type="text" id="input-with-text" class="form-control" placeholder="Username">
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-icon" class="form-label">Input with Icon</label>
      <div class="input-group">
        <span class="input-group-text"><i class="fas fa-envelope"></i></span>
        <input type="email" id="input-with-icon" class="form-control" placeholder="Email address">
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-button" class="form-label">Input with Button</label>
      <div class="input-group">
        <input type="text" id="input-with-button" class="form-control" placeholder="Search term">
        <button class="btn btn-primary" type="button">Search</button>
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-both" class="form-label">Input with Both Addons</label>
      <div class="input-group">
        <span class="input-group-text">$</span>
        <input type="number" id="input-with-both" class="form-control" placeholder="Amount">
        <span class="input-group-text">.00</span>
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-dropdown" class="form-label">Input with Dropdown</label>
      <div class="input-group">
        <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">Dropdown</button>
        <ul class="dropdown-menu">
          <li><a class="dropdown-item" href="#">Action</a></li>
          <li><a class="dropdown-item" href="#">Another action</a></li>
          <li><a class="dropdown-item" href="#">Something else here</a></li>
        </ul>
        <input type="text" id="input-with-dropdown" class="form-control" placeholder="Text input">
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-checkbox" class="form-label">Input with Checkbox</label>
      <div class="input-group">
        <div class="input-group-text">
          <input class="form-check-input" type="checkbox" aria-label="Checkbox for following text input">
        </div>
        <input type="text" id="input-with-checkbox" class="form-control" placeholder="Text input with checkbox">
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <label for="input-with-radio" class="form-label">Input with Radio</label>
      <div class="input-group">
        <div class="input-group-text">
          <input class="form-check-input" type="radio" aria-label="Radio button for following text input">
        </div>
        <input type="text" id="input-with-radio" class="form-control" placeholder="Text input with radio button">
      </div>
    </div>
  </div>
`;

export const FormValidation = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/form-elements.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Form Validation Examples</h2>
    
    <form class="needs-validation" novalidate style="margin-top: 24px;">
      <div class="mb-3">
        <label for="validation-name" class="form-label required">Full Name</label>
        <input type="text" class="form-control" id="validation-name" required>
        <div class="invalid-feedback">
          Please enter your full name.
        </div>
      </div>
      
      <div class="mb-3">
        <label for="validation-email" class="form-label required">Email</label>
        <input type="email" class="form-control" id="validation-email" required>
        <div class="invalid-feedback">
          Please enter a valid email address.
        </div>
      </div>
      
      <div class="mb-3">
        <label for="validation-phone" class="form-label">Phone Number</label>
        <input type="tel" class="form-control" id="validation-phone" pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}">
        <div class="form-text">Format: 123-456-7890</div>
        <div class="invalid-feedback">
          Please enter a valid phone number in the format XXX-XXX-XXXX.
        </div>
      </div>
      
      <div class="mb-3">
        <label for="validation-password" class="form-label required">Password</label>
        <input type="password" class="form-control" id="validation-password" required minlength="8">
        <div class="invalid-feedback">
          Password must be at least 8 characters long.
        </div>
      </div>
      
      <div class="mb-3">
        <label for="validation-select" class="form-label required">Role</label>
        <select class="form-select" id="validation-select" required>
          <option value="">Select a role</option>
          <option value="admin">Administrator</option>
          <option value="user">Regular User</option>
          <option value="editor">Editor</option>
        </select>
        <div class="invalid-feedback">
          Please select a role.
        </div>
      </div>
      
      <div class="mb-3">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="validation-terms" required>
          <label class="form-check-label" for="validation-terms">
            I agree to the terms and conditions
          </label>
          <div class="invalid-feedback">
            You must agree before submitting.
          </div>
        </div>
      </div>
      
      <button class="btn btn-primary" type="submit">Submit form</button>
    </form>
  </div>
`; 