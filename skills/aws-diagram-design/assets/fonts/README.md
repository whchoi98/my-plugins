# Amazon Ember — bundled fonts

Amazon Ember (and Amazon Ember Mono) as distributed by Amazon at
<https://developer.amazon.com/en-US/alexa/branding/echo-guidelines/identity-guidelines/typography>
(`Amazon_Typefaces_Complete_Font_Set_Mar2020.zip`). Usage terms:
[`Amazon-Ember-Licensing-Guidelines.pdf`](Amazon-Ember-Licensing-Guidelines.pdf) in this directory.

## Inventory

| File (woff2/) | Family | Weight / style |
|---|---|---|
| `AmazonEmber_W_Lt.woff2` | Amazon Ember | 300 |
| `AmazonEmber_W_Rg.woff2` | Amazon Ember | 400 |
| `AmazonEmber_W_RgIt.woff2` | Amazon Ember | 400 italic |
| `AmazonEmber_W_SBd.woff2` | Amazon Ember | 600 |
| `AmazonEmber_W_Bd.woff2` | Amazon Ember | 700 |
| `AmazonEmber_W_He.woff2` | Amazon Ember | 800 |
| `AmazonEmberMono_W_Rg.woff2` | Amazon Ember Mono | 400 |
| `AmazonEmberMono_W_Bd.woff2` | Amazon Ember Mono | 700 |

`ttf/` carries the desktop faces (Ember Lt/Rg/RgIt/Medium/Bd/He + Ember Mono Rg/Bd). `/my-plugins:setup`
copies them into the user's font folder.

## How a diagram uses them

The font source of the AWS skin is `system` (`references/style-guide.md`, Font source): a diagram names the
families and the installed faces answer. A diagram carries no font `<link>`, no `@import` and no CSS `url()`;
`scripts/self_check.py` rejects a `url()` that is not a fragment, and `scripts/aws_check.py` rejects a font
loaded from outside the file. Always keep the fallback stacks on `font-family`
(`'Helvetica Neue', Helvetica, Arial, sans-serif` for Ember; `ui-monospace, monospace` for Ember Mono): a
machine without the fonts, or a viewer that blocks them such as GitHub's SVG sandbox, falls back to system faces.

## Optional @font-face block (installed faces only)

Without it a weight the installed faces do not have snaps to the nearest one: a 600 node name renders in Bold.
This block maps 600 to the Medium face. It names installed faces with `local()` only, so it loads nothing:

```css
@font-face { font-family: 'Amazon Ember'; font-weight: 300; font-style: normal;
  src: local('Amazon Ember Light'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 400; font-style: normal;
  src: local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 400; font-style: italic;
  src: local('Amazon Ember Italic'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 600; font-style: normal;
  src: local('Amazon Ember Medium'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 700; font-style: normal;
  src: local('Amazon Ember Bold'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember'; font-weight: 800; font-style: normal;
  src: local('Amazon Ember Heavy'), local('Amazon Ember'); }
@font-face { font-family: 'Amazon Ember Mono'; font-weight: 400; font-style: normal;
  src: local('Amazon Ember Mono'); }
@font-face { font-family: 'Amazon Ember Mono'; font-weight: 700; font-style: normal;
  src: local('Amazon Ember Mono Bold'), local('Amazon Ember Mono'); }
```

The `woff2/` files are for a page that is served with its fonts beside it, such as a web site. A diagram is one
self-contained file and does not reference them.
