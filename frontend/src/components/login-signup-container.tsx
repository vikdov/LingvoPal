function container(){
    return
    <>
<div class="language-selector">
<select>
<option value="en">English</option>
<option value="zh">Polski</option>
<option value="de">Deutsch</option>
<option value="es">Español</option>
</select>
</div>

<div class="container">
<div class="logo">
<h1>Lingv<span><img class="globe"src="img/earth-americas-solid.svg" alt=""></span><span>Pal</span></h1>
<p>Your language learning companion</p>
</div>

<h2>Sign in to LingvoPal</h2>

<form>
<div class="form-group">
<label for="email">Email</label>
<input type="email" id="email" placeholder="Enter your email" required>
</div>

<div class="form-group">
<label for="password">Password</label>
<input type="password" id="password" placeholder="Enter your password" required>
</div>

<div class="forgot-password">
<a href="passwordreset.html">Forgot password?</a>
</div>

<button type="submit">Sign In</button>
<p class="checkbox-group">By signing in, I agree to the LingvoPal's <a href="privacy-statement.html"> Privacy Statement</a> and <a href="terms-of-service.html">Terms of Service</a>.</p>

</form>

<div class="or-divider">
<span>Or sign up with</span>
</div>

<div class="social-login">
<div class="social-btn">
<a href="https://www.google.com/"><img class="social-img" src="img/google.png" alt="Google login method"></a>
</div>
<div class="social-btn">
<a href="https://www.facebook.com/"><img class="social-img" src="img/facebook.png" alt="Facebook login method"></a>
</div>
<div class="social-btn">
<a href="https://www.apple.com/"><img class="social-img" src="img/appleid.png" alt="Apple ID login method"></a>
</div>
</div>

<div class="signup-link">
Don't have an account? <a href="signup.html">Sign up for free</a>
</div>
</div>
</>

}
