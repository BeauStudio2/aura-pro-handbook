# Aura Pro handbook

Open [the introduction](index.html) in a browser. The handbook uses plain HTML, local diagrams, images, and fonts. It also works offline.

The home page also contains the [full chapter directory](index.html#chapters). When adding a chapter, include its link and a short topic description there and on the section page where a reader would look for it. Place searchable sections inside their chapter’s nested `section-hits` list. Use the destination heading as the link text, link to its fragment, and include ordinary search terms in `data-keywords`. Hide the list and its entries initially. Search combines section and chapter terms and shows matching sections under the chapter link. Check a route from home using the words a reader would bring to the handbook.

## Where to edit

- [Introduction](index.html) contains the approved product introduction.
- [Cognitive map](map.html) contains the shared logic and the open architecture questions.
- [Reasoning patterns](patterns/index.html) links seven chapters, each pairing an abstract decision process with the example that illustrates it.
- [System capabilities](capabilities/index.html) proposes ten architecture responsibilities. Each page defines inputs and outputs, links the relevant patterns and neighboring capabilities, and has a section for approach, execution, and technology choices.
- [Construction tools and integration](capabilities/integration.html) describes record ownership, replaceable adapters, and how an existing client workflow can move into Aura Pro.

For the next analysis, edit the relevant capability's existing HTML page. Describe the reasoning approach, trace an execution from input to observable output, and evaluate stack choices against that workflow. Keep its filename stable so existing links continue to work. When a responsibility changes, update the connected capability pages as well.

The handbook is a static edition of the core product identity and cognitive-map documents. Update the corresponding HTML and diagram when revising the source material. Shared presentation is in `assets/handbook.css`.

## Publish on GitHub Pages

1. Place the **contents** of this folder at the root of your intended Pages publishing branch. Keep the `assets`, `patterns`, and `capabilities` directories alongside `index.html`.
2. In the repository's **Settings → Pages**, choose **Deploy from a branch**, select that branch and **/(root)**, and save.
3. Open the URL GitHub reports after deployment. Links are relative and work under a repository subpath.

GitHub also supports a Pages workflow that uploads this directory as its site artifact. [GitHub Pages publishing options](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
