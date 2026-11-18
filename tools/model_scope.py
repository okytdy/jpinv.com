"""Keep the maintained public forecast library within simulated holdings."""
import json


def portfolio_models(root, models):
    snapshot = json.loads((root / 'en/portfolio/portfolio-data.json').read_text('utf-8'))
    held = {str(h['ticker']) for h in snapshot['snapshot']['holdings'] if h['shares'] > 0}
    outside = {m['ticker'] for m in models} - held
    if outside:
        raise ValueError('Public forecast models require a simulated holding: ' + ', '.join(sorted(outside)))
    return models
