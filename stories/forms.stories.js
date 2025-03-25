import { html } from 'lit-html';

export default {
  title: 'Components/Forms',
};

export const FormElements = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem; max-width: 800px;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Form Elements</h1>
      
      <h2 style="margin-top: 2rem;">Text Input</h2>
      <div style="margin-bottom: 2rem;">
        <div class="form-group">
          <label for="textInput" class="form-label">Text Input</label>
          <input type="text" class="form-control" id="textInput" placeholder="Enter text">
          <div class="form-text">Helper text for this input field.</div>
        </div>
        
        <div class="form-group">
          <label for="disabledInput" class="form-label">Disabled Input</label>
          <input type="text" class="form-control" id="disabledInput" placeholder="Disabled input" disabled>
        </div>
        
        <div class="form-group">
          <label for="readonlyInput" class="form-label">Readonly Input</label>
          <input type="text" class="form-control" id="readonlyInput" value="Readonly input" readonly>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Input Validation States</h2>
      <div style="margin-bottom: 2rem;">
        <div class="form-group">
          <label for="validInput" class="form-label">Valid Input</label>
          <input type="text" class="form-control is-valid" id="validInput" value="Valid input">
          <div class="valid-feedback">Looks good!</div>
        </div>
        
        <div class="form-group">
          <label for="invalidInput" class="form-label">Invalid Input</label>
          <input type="text" class="form-control is-invalid" id="invalidInput" value="Invalid input">
          <div class="invalid-feedback">Please provide valid input.</div>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Select</h2>
      <div style="margin-bottom: 2rem;">
        <div class="form-group">
          <label for="selectDefault" class="form-label">Default Select</label>
          <select class="form-select" id="selectDefault">
            <option selected>Choose an option</option>
            <option value="1">Option 1</option>
            <option value="2">Option 2</option>
            <option value="3">Option 3</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="selectMultiple" class="form-label">Multiple Select</label>
          <select class="form-select" id="selectMultiple" multiple>
            <option value="1">Option 1</option>
            <option value="2">Option 2</option>
            <option value="3">Option 3</option>
            <option value="4">Option 4</option>
          </select>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Textarea</h2>
      <div style="margin-bottom: 2rem;">
        <div class="form-group">
          <label for="textareaDefault" class="form-label">Textarea</label>
          <textarea class="form-control" id="textareaDefault" rows="3" placeholder="Enter text"></textarea>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Checkboxes</h2>
      <div style="margin-bottom: 2rem;">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="checkbox1">
          <label class="form-check-label" for="checkbox1">Default checkbox</label>
        </div>
        
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="checkbox2" checked>
          <label class="form-check-label" for="checkbox2">Checked checkbox</label>
        </div>
        
        <div class="form-check">
          <input class="form-check-input" type="checkbox" id="checkbox3" disabled>
          <label class="form-check-label" for="checkbox3">Disabled checkbox</label>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Radio Buttons</h2>
      <div style="margin-bottom: 2rem;">
        <div class="form-check">
          <input class="form-check-input" type="radio" name="radios" id="radio1" checked>
          <label class="form-check-label" for="radio1">
            Default radio
          </label>
        </div>
        
        <div class="form-check">
          <input class="form-check-input" type="radio" name="radios" id="radio2">
          <label class="form-check-label" for="radio2">
            Second radio
          </label>
        </div>
        
        <div class="form-check">
          <input class="form-check-input" type="radio" name="radios" id="radio3" disabled>
          <label class="form-check-label" for="radio3">
            Disabled radio
          </label>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Input Groups</h2>
      <div style="margin-bottom: 2rem;">
        <div class="input-group mb-3">
          <span class="input-group-text">@</span>
          <input type="text" class="form-control" placeholder="Username">
        </div>
        
        <div class="input-group mb-3">
          <input type="text" class="form-control" placeholder="Recipient's username">
          <span class="input-group-text">@example.com</span>
        </div>
        
        <div class="input-group mb-3">
          <span class="input-group-text">$</span>
          <input type="text" class="form-control" placeholder="Amount">
          <span class="input-group-text">.00</span>
        </div>
      </div>
    </div>
  `;
};

export const FormLayout = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem; max-width: 800px;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Form Layout</h1>
      
      <h2 style="margin-top: 2rem;">Basic Form</h2>
      <form style="margin-bottom: 2rem;">
        <div class="form-group">
          <label for="exampleEmail" class="form-label">Email address</label>
          <input type="email" class="form-control" id="exampleEmail" placeholder="name@example.com">
        </div>
        
        <div class="form-group">
          <label for="examplePassword" class="form-label">Password</label>
          <input type="password" class="form-control" id="examplePassword" placeholder="Password">
        </div>
        
        <div class="form-check mb-3">
          <input class="form-check-input" type="checkbox" id="rememberCheck">
          <label class="form-check-label" for="rememberCheck">
            Remember me
          </label>
        </div>
        
        <button type="submit" class="btn btn-primary">Submit</button>
      </form>
      
      <h2 style="margin-top: 2rem;">Horizontal Form</h2>
      <form style="margin-bottom: 2rem;">
        <div class="row mb-3">
          <label for="horizontalEmail" class="col-sm-2 col-form-label">Email</label>
          <div class="col-sm-10">
            <input type="email" class="form-control" id="horizontalEmail">
          </div>
        </div>
        
        <div class="row mb-3">
          <label for="horizontalPassword" class="col-sm-2 col-form-label">Password</label>
          <div class="col-sm-10">
            <input type="password" class="form-control" id="horizontalPassword">
          </div>
        </div>
        
        <div class="row mb-3">
          <div class="col-sm-10 offset-sm-2">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="horizontalCheck">
              <label class="form-check-label" for="horizontalCheck">
                Remember me
              </label>
            </div>
          </div>
        </div>
        
        <div class="row">
          <div class="col-sm-10 offset-sm-2">
            <button type="submit" class="btn btn-primary">Sign in</button>
          </div>
        </div>
      </form>
      
      <h2 style="margin-top: 2rem;">Form Guidelines</h2>
      <div style="margin-bottom: 2rem;">
        <ul>
          <li>Group related fields together</li>
          <li>Use clear, concise labels</li>
          <li>Indicate required fields</li>
          <li>Provide helpful validation messages</li>
          <li>Use appropriate input types for different data</li>
          <li>Include form-level error summaries for accessibility</li>
          <li>Maintain a logical tab order</li>
        </ul>
      </div>
    </div>
  `;
};

export const FormValidation = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem; max-width: 800px;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Form Validation</h1>
      
      <h2 style="margin-top: 2rem;">Client-Side Validation</h2>
      <form class="was-validated" style="margin-bottom: 2rem;">
        <div class="form-group">
          <label for="validationName" class="form-label">Name</label>
          <input type="text" class="form-control" id="validationName" placeholder="Enter your name" required>
          <div class="invalid-feedback">
            Please provide your name.
          </div>
        </div>
        
        <div class="form-group">
          <label for="validationEmail" class="form-label">Email</label>
          <input type="email" class="form-control" id="validationEmail" placeholder="Enter your email" required>
          <div class="invalid-feedback">
            Please provide a valid email address.
          </div>
        </div>
        
        <div class="form-group">
          <label for="validationSelect" class="form-label">Select Option</label>
          <select class="form-select" id="validationSelect" required>
            <option value="">Choose...</option>
            <option value="1">Option 1</option>
            <option value="2">Option 2</option>
            <option value="3">Option 3</option>
          </select>
          <div class="invalid-feedback">
            Please select an option.
          </div>
        </div>
        
        <div class="form-group">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="validationCheck" required>
            <label class="form-check-label" for="validationCheck">
              Agree to terms and conditions
            </label>
            <div class="invalid-feedback">
              You must agree before submitting.
            </div>
          </div>
        </div>
        
        <button class="btn btn-primary" type="submit">Submit form</button>
      </form>
      
      <h2 style="margin-top: 2rem;">Validation Guidelines</h2>
      <div style="margin-bottom: 2rem;">
        <ul>
          <li>Validate in real-time when possible</li>
          <li>Show error messages next to the field with errors</li>
          <li>Use both color and text to indicate errors</li>
          <li>Be specific about what is wrong and how to fix it</li>
          <li>Don't clear form data when validation fails</li>
          <li>Ensure error messages are accessible</li>
        </ul>
      </div>
    </div>
  `;
}; 