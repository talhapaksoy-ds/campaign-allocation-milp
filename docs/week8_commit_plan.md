# Suggested Week 8 Commit Plan

The assignment asks for at least 5 commits. The following commit sequence can be used after copying the files into the repository.

```bash
git checkout -b week8-mdp-update

git add reports/Deliverable5.pdf
git commit -m "Add Week 8 MDP deliverable report"

git add mdp_notes.md
git commit -m "Add MDP formulation notes"

git add src/mdp.py
git commit -m "Add draft MDP representation"

git add src/dp.py src/policy_evaluation.py
git commit -m "Add draft dynamic programming and policy evaluation files"

git add README.md
git commit -m "Update README with Week 8 MDP interpretation"

git push origin week8-mdp-update
```

After pushing, a pull request can be opened or the branch can be merged into `main`.

If committing directly to `main`, remove the branch commands and use:

```bash
git push origin main
```
