<script lang="ts">
  import ContactUsDialog from "$lib/components/ContactUsDialog.svelte";
  import DisclaimerDialog from "$lib/components/DisclaimerDialog.svelte";

  let contactOpen = false;
  let disclaimerOpen = false;
</script>  

<footer class="footer-section bg-[#16306b] text-white" role="contentinfo" aria-label="Footer">
  <div class="container-fluid w-full px-6 pt-4 pb-0">
    <div class="footer-inner max-w-[1200px] mx-auto grid md:grid-cols-2 gap-6 md:gap-x-20 gap-y-6 items-start">
    <div>
      <h3 class="footer-left-heading font-semibold text-lg mb-3"> USEFUL LINKS</h3>
      <div class="row links-wrap align-items-end">
        <div class="footer-link-block text-sm">
          <!-- About DI Lab removed as requested -->
          <nav class="footer-links" aria-label="Useful links">
            <a tabindex="-1" href="https://www.datainnovation.mospi.gov.in/website-policy" target="_blank" rel="noopener noreferrer" class="hover:underline">Privacy policy</a>
            <a tabindex="-1" href="https://www.datainnovation.mospi.gov.in/help" target="_blank" rel="noopener noreferrer" class="hover:underline">Help</a>
            <a tabindex="-1" href="#" class="hover:underline" on:click|preventDefault={() => { disclaimerOpen = true }}>Disclaimer</a>
            <a tabindex="-1" href="#" class="hover:underline" on:click|preventDefault={() => { contactOpen = true }}>Contact Us</a>
            <a tabindex="-1" href="https://www.datainnovation.mospi.gov.in/sitemap" target="_blank" rel="noopener noreferrer" class="hover:underline">Sitemap</a>
            <a tabindex="-1" href="https://mospi.gov.in/" target="_blank" rel="noopener noreferrer" class="hover:underline">MoSPI Website</a>
            <a tabindex="-1" href="https://esankhyiki.mospi.gov.in/" target="_blank" rel="noopener noreferrer" class="hover:underline">eSankhyiki Website</a>
            <a tabindex="-1" href="https://microdata.gov.in/" target="_blank" rel="noopener noreferrer" class="hover:underline">Micro Data Website</a>
            <a tabindex="-1" href="https://www.datainnovation.mospi.gov.in/related-links" target="_blank" rel="noopener noreferrer" class="hover:underline">Related links</a>
            <a tabindex="-1" href="#" class="hover:underline" on:click|preventDefault={() => { contactOpen = true }}>Feedback</a>
            <a tabindex="-1" href="https://www.datainnovation.mospi.gov.in/archives" target="_blank" rel="noopener noreferrer" class="hover:underline">Archives</a>
            <a tabindex="-1" href="https://darpg.gov.in/sites/default/files/PGR_Guideline.pdf" target="_blank" rel="noopener noreferrer" class="hover:underline">Public Grievance Redressal Mechanism</a>
          </nav>
        </div>
      </div>
    </div>

    <div>
      <h3 class="footer-right-heading font-semibold text-lg mb-3"> SUBSCRIBE FOR UPDATES</h3>
      <ul class="list-unstyled flex items-center gap-4 mb-3">
        <li>
          <a href="https://twitter.com/GoIStats?s=08" tabindex="-1" target="_blank" rel="noopener" aria-label="Twitter">
            <svg class="social-icons h-8 w-8" viewBox="0 -223.685 1668.56 1668.56" original_string_length="542"><path d="M283.94,167.31l386.39,516.64L281.5,1104h87.51l340.42-367.76L984.48,1104h297.8L874.15,558.3l361.92-390.99 h-87.51l-313.51,338.7l-253.31-338.7H283.94z M412.63,231.77h136.81l604.13,807.76h-136.81L412.63,231.77z" transform="translate(52.39 -25.059)" style="fill: currentColor;"></path></svg>
          </a>
        </li>
        <li>
          <a href="https://www.facebook.com/GoIStats/" tabindex="-1" target="_blank" rel="noopener" aria-label="Facebook">
            <svg class="social-icons h-8 w-8" viewBox="126.445 2.281 589 589" original_string_length="629"><circle cx="420.945" cy="296.781" r="294.5" style="fill: rgb(255, 255, 255);"></circle><path d="M516.704 92.677h-65.239c-38.715 0-81.777 16.283-81.777 72.402.189 19.554 0 38.281 0 59.357H324.9v71.271h46.174v205.177h84.847V294.353h56.002l5.067-70.117h-62.531s.14-31.191 0-40.249c0-22.177 23.076-20.907 24.464-20.907 10.981 0 32.332.032 37.813 0V92.677h-.032z" style="fill: rgb(22, 46, 106);"></path></svg>
          </a>
        </li>
        <li>
          <a href="https://www.instagram.com/goistats/?igshid=1ea2ccd5gsb85" tabindex="-1" target="_blank" rel="noopener" aria-label="Instagram">
            <svg class="social-icons h-8 w-8" data-name="Layer 1" viewBox="0 0 24 24"><path d="M12,9.52A2.48,2.48,0,1,0,14.48,12,2.48,2.48,0,0,0,12,9.52Zm9.93-2.45a6.53,6.53,0,0,0-.42-2.26,4,4,0,0,0-2.32-2.32,6.53,6.53,0,0,0-2.26-.42C15.64,2,15.26,2,12,2s-3.64,0-4.93.07a6.53,6.53,0,0,0-2.26.42A4,4,0,0,0,2.49,4.81a6.53,6.53,0,0,0-.42,2.26C2,8.36,2,8.74,2,12s0,3.64.07,4.93a6.86,6.86,0,0,0,.42,2.27,3.94,3.94,0,0,0,.91,1.4,3.89,3.89,0,0,0,1.41.91,6.53,6.53,0,0,0,2.26.42C8.36,22,8.74,22,12,22s3.64,0,4.93-.07a6.53,6.53,0,0,0,2.26-.42,3.89,3.89,0,0,0,1.41-.91,3.94,3.94,0,0,0,.91-1.4,6.6,6.6,0,0,0,.42-2.27C22,15.64,22,15.26,22,12S22,8.36,21.93,7.07Zm-2.54,8A5.73,5.73,0,0,1,19,16.87,3.86,3.86,0,0,1,16.87,19a5.73,5.73,0,0,1-1.81.35c-.79,0-1,0-3.06,0s-2.27,0-3.06,0A5.73,5.73,0,0,1,7.13,19a3.51,3.51,0,0,1-1.31-.86A3.51,3.51,0,0,1,5,16.87a5.49,5.49,0,0,1-.34-1.81c0-.79,0-1,0-3.06s0-2.27,0-3.06A5.49,5.49,0,0,1,5,7.13a3.51,3.51,0,0,1,.86-1.31A3.59,3.59,0,0,1,7.13,5a5.73,5.73,0,0,1,1.81-.35h0c.79,0,1,0,3.06,0s2.27,0,3,0A5.73,5.73,0,0,1,16.87,5a3.51,3.51,0,0,1,1.31.86A3.51,3.51,0,0,1,19,7.13a5.73,5.73,0,0,1,.35,1.81c0,.79,0,1,0,3.06S19.42,14.27,19.39,15.06Zm-1.6-7.44a2.38,2.38,0,0,0-1.41-1.41A4,4,0,0,0,15,6c-.78,0-1,0-3,0s-2.22,0-3,0a4,4,0,0,0-1.38.26A2.38,2.38,0,0,0,6.21,7.62,4.27,4.27,0,0,0,6,9c0,.78,0,1,0,3s0,2.22,0,3a4.27,4.27,0,0,0,.26,1.38,2.38,2.38,0,0,0,1.41,1.41A4.27,4.27,0,0,0,9,18.05H9c.78,0,1,0,3,0s2.22,0,3,0a4,4,0,0,0,1.38-.26,2.38,2.38,0,0,0,1.41-1.41A4,4,0,0,0,18.05,15c0-.78,0-1,0-3s0-2.22,0-3A3.78,3.78,0,0,0,17.79,7.62ZM12,15.82A3.81,3.81,0,0,1,8.19,12h0A3.82,3.82,0,1,1,12,15.82Zm4-6.89a.9.9,0,0,1,0-1.79h0a.9.9,0,0,1,0,1.79Z" style="fill: currentColor;"></path></svg>
          </a>
        </li>
        <li>
          <a href="https://www.youtube.com/@GoIStats" tabindex="-1" target="_blank" rel="noopener" aria-label="YouTube">
            <svg class="social-icons h-8 w-8" data-name="Layer 1" viewBox="0 0 24 24" original_string_length="755" style="fill: rgb(255, 255, 255);"><path d="M23,9.71a8.5,8.5,0,0,0-.91-4.13,2.92,2.92,0,0,0-1.72-1A78.36,78.36,0,0,0,12,4.27a78.45,78.45,0,0,0-8.34.3,2.87,2.87,0,0,0-1.46.74c-.9.83-1,2.25-1.1,3.45a48.29,48.29,0,0,0,0,6.48,9.55,9.55,0,0,0,.3,2,3.14,3.14,0,0,0,.71,1.36,2.86,2.86,0,0,0,1.49.78,45.18,45.18,0,0,0,6.5.33c3.5.05,6.57,0,10.2-.28a2.88,2.88,0,0,0,1.53-.78,2.49,2.49,0,0,0,.61-1,10.58,10.58,0,0,0,.52-3.4C23,13.69,23,10.31,23,9.71ZM9.74,14.85V8.66l5.92,3.11C14,12.69,11.81,13.73,9.74,14.85Z"></path></svg>
          </a>
        </li>
      </ul>

      <div class="ownership text-sm text-white/90 mt-2">
        <p>Contents of this website owned and managed by Data Innovation Lab, MoSPI</p>
        <p>Designed, Developed and Hosted by DIID, MoSPI</p>
        <p>Copyright© 2026 All Rights Reserved.</p>
      </div>
    </div>
  </div>
  </div>

  <ContactUsDialog bind:open={contactOpen} />
  <DisclaimerDialog bind:open={disclaimerOpen} />
</footer>

<style>
  footer a { color: rgba(255,255,255,0.95); }
  footer a:hover { text-decoration: underline; }
  .footer-section { position: static; background-color: #16306b; padding-top: 0.5rem; padding-bottom: 0.5rem; }

  /* Centered inner content so background spans full width but content remains tidy */
  .footer-inner { max-width: 1200px; margin: 0 auto; }

  .footer-left-heading, .footer-right-heading { text-transform: uppercase; font-weight: 700; letter-spacing: 0.02em; font-size: 1.05rem; margin-bottom: 0.6rem; }

  .footer-links { display:flex; flex-wrap:wrap; gap:0.375rem 0.9rem; align-items:center; }
  .footer-links a { font-weight:600; font-size:0.92rem; color: rgba(255,255,255,0.95); }
  .footer-links a:not(:last-child)::after { content: '|'; color: rgba(255,255,255,0.36); margin-left: 0.6rem; margin-right: 0.6rem; }

  .footer-right { display:flex; flex-direction:column; gap:0.75rem; align-items:flex-start; padding-left: 1.5rem; }
  .social-list { display:flex; gap:0.75rem; align-items:center; }

  .social-icons { color: #ffffff; fill: currentColor; width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; background: transparent; padding: 0; border-radius:9999px; transition: transform 0.08s; }
  .social-icons:hover { transform: translateY(-1px); }

  .ownership p { margin: 0; font-size: 0.88rem; line-height: 1.4; color: rgba(255,255,255,0.9); }

  @media (max-width: 768px) { .footer-right { padding-left: 0; } }

  p.text-sm.leading-relaxed { margin: 0; font-size: 0.98rem; color: rgba(255,255,255,0.92); }

  /* Centered inner content so background spans full width but content remains tidy */
  .footer-inner { max-width: 1200px; margin: 0 auto; }

  .footer-left-heading, .footer-right-heading { text-transform: uppercase; font-weight: 700; letter-spacing: 0.02em; font-size: 1.05rem; margin-bottom: 0.6rem; }

  .footer-links { display:flex; flex-wrap:wrap; gap:0.375rem 0.9rem; align-items:center; }
  .footer-links a { font-weight:600; font-size:0.92rem; color: rgba(255,255,255,0.95); }
  .footer-links a:not(:last-child)::after { content: '|'; color: rgba(255,255,255,0.36); margin-left: 0.6rem; margin-right: 0.6rem; }

  .footer-right { display:flex; flex-direction:column; gap:0.75rem; align-items:flex-start; padding-left: 1.5rem; }
  .social-list { display:flex; gap:0.75rem; align-items:center; }

  .social-icons { color: #ffffff; fill: currentColor; width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; background: transparent; padding: 0; border-radius:9999px; transition: transform 0.08s; }
  .social-icons:hover { transform: translateY(-1px); }

  .ownership p { margin: 0; font-size: 0.88rem; line-height: 1.4; color: rgba(255,255,255,0.9); }

  @media (max-width: 768px) { .footer-right { padding-left: 0; } }

  p.text-sm.leading-relaxed { margin: 0; font-size: 0.98rem; color: rgba(255,255,255,0.92); }
</style>