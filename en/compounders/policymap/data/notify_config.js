/* JII Policy Map - milestone-alert signup config.
   The "Get notified" block on the Policy Map renders an inline email form that
   posts directly to MailerLite (mlAction), adding subscribers to the
   "Policy Map milestones" group with double opt-in. No external page.
   If mlAction is blank, the block falls back to an email to mailto.
   Keep this file identical in /en/ and the JA copy. */
window.PM_NOTIFY = {
  mailto: "info@jpinv.com",
  mlAction: "https://assets.mailerlite.com/jsonp/2399905/forms/189168376316167324/subscribe"
};
