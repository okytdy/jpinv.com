/* JII Policy Map — milestone-alert signup config.
   Goal: collect subscribers in MailerLite and send alerts as info@jpinv.com.

   To go live, set formUrl to your MailerLite form's PUBLIC URL:
     MailerLite > Forms > (create/select your form) > Share > copy the public URL
     (looks like  https://your-handle.mailerlite.com/xxxxxxxxx ).
   Paste it below, commit, and push. Until then the Notify button falls back to
   an email to info@jpinv.com, so nothing is broken in the meantime.

   Keep this file identical in /en/ and the JA copy. */
window.PM_NOTIFY = {
  mailto: "info@jpinv.com",
  formUrl: ""   // <-- paste MailerLite public form URL here, e.g. "https://jii.mailerlite.com/abc123"
};
