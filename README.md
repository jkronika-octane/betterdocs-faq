# BetterDocs FAQ Scraper

This project provides a script that will attempt to scrape pages under a given domain and path on the web, assuming that
the pages there contain some amount of content written using the BetterDocs plugin for Wordpress.

While technically this can be used to scrape any site using BetterDocs, it was primarily written to scrape content built
for the purposes of Frequently Asked Questions - one question per page, with a single dedicated answer for each. There
is some additional functionality supporting a page containing a collection of related questions and answers, but that
relies upon specific markup.

## Dependencies

* In order to pull down content from the provided web property, the `wget` tool must be installed and able to be
  executed as a subprocess by Python.
* The packages needed for the Python script itself are listed in the included `requirements.txt` file.
* Python 3.13 has been fully tested with this script, but other versions of Python may work as well, so long as they are
  compatible with the required packages.

## Execution

To get the most up-to-date usage instructions, ask for help:

```shell
python betterdocs_faq/scraper.py --help
```

In its most basic form, we simply provide a `--domain` (`-d`) and `--path` (`-p`) to the script, and it will handle the
rest using sensible defaults where necessary.

## Legal notice and acceptable use

* This tool issues automated HTTP requests and can recursively download content. You are solely responsible for how you
  use it. Ensure you have authorization to access and copy the target content and that your use complies with all
  applicable laws and third‑party terms.
* You must:
    * Comply with the target site’s terms of service and any specific written requests to stop (including
      cease‑and‑desist letters). If a site blocks or rate‑limits you, do not attempt to evade those measures.
    * Avoid accessing pages or data behind logins, paywalls, or technical access controls, and do not bypass CAPTCHAs or
      other access restrictions.
    * Respect the Robots Exclusion Standard and rate limits unless you have explicit permission to do otherwise; set
      conservative wait/concurrency values to avoid burdening servers.
    * Refrain from collecting, storing, or sharing personal data unless you have a lawful basis and provide all required
      notices under applicable privacy and data‑protection laws.
* Third‑party tools: This project may invoke external programs (e.g., `wget`). Their licenses and terms apply in
  addition to this project’s license. Consult those upstream terms before distribution or embedding.
* No legal advice: Nothing here is legal advice. Consult your own counsel before using this tool on third‑party systems
  or data.
* Disclaimer; allocation of risk: The software is provided under the MIT License (see LICENSE) “AS IS,” without
  warranties of any kind. To the maximum extent permitted by law, you assume all risk arising from use. The authors are
  not liable for any claims or damages arising out of or related to your use.
* Indemnity: To the maximum extent permitted by law, you agree to defend, indemnify, and hold harmless the authors and
  contributors from and against any third‑party claims arising from your use of the software.