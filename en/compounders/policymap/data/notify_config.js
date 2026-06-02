/* JII Policy Map - milestone-alert signup config.
   The "Notify me" button on the Policy Map opens formUrl (a MailerLite hosted
   signup page that adds subscribers to the "Policy Map milestones" group, with
   double opt-in). If formUrl is ever blank, the button falls back to emailing
   mailto. Keep this file identical in /en/ and the JA copy. */
window.PM_NOTIFY = {
  mailto: "info@jpinv.com",
  formUrl: "https://jii-policy-map.subscribepage.io"
};
