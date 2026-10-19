# Atomic capability catalog

Use [operation-catalog.json](operation-catalog.json) to decompose a request or plan
an operation implementation. Select executable templates through
[operation-registry.json](operation-registry.json). The catalog covers the approved
139 actions: GU 20, MS 11, MA 35, EX 14, ER 12, VA 25, VI 22.

## Reading an entry

`id` is a stable planning identifier. `operation` is a descriptive key within its
stage. `name` is the review label. `inputs`, `output`, `preconditions`, and
`postcondition` define one engineering effect; they are catalog-level contracts,
not a finished implementation. `implementation_scope` states any narrower scope
of the current template. An input supplied by the caller need not be produced by
another registered atom.

`topology_effect` describes changes to modeled geometry: `none`, `creates`,
`modifies`, `deletes`, or `conditional`. Movement, naming, file deletion, viewport
changes, and replacing an entire document are distinguished from changing an
existing body's topology. `conditional` requires the future implementation to
declare the applicable effect. Refresh object references after changes that can
invalidate them.

`required_evidence` lists evidence to obtain for the planned capability. It is
not a passed result. `interpretation_evaluation` denotes a source-grounded
evaluation of a reasoning action; it adds no layer to existing runtime-report or
template schemas. Source evaluation artifacts can support a later template's
host evidence only with an explicit scope. All other evidence names retain the
architecture's meanings. Evidence needs may be specialized to a fixed variant
without claiming untested alternatives.

## Lifecycle and routing

- `catalogued`: defined action only; `registry_operation_id` is null.
- `candidate`: a registry template exists; its scope and evidence remain limited.
- `active`: a registry template may be selected when its preconditions match.
- `deprecated`: a registered implementation has a replacement or fallback route.

Every registered operation maps to exactly one catalog entry. The catalog copies
its lifecycle for discovery; the registry and referenced template remain the
authority for execution and exact evidence. A future lifecycle change must update
both records together. A catalogued action may still be performed through the
generic v0.2 workflow, with its actual evidence reported; cataloguing neither
removes that capability nor grants a template runtime claim.

## Granularity and overlap

One main effect may need several API calls, parameter fields, or precondition
checks. Whole parts, completed geometry contracts, complete scripts, whole
execution transactions, and multi-view acceptance are compositions. Parameterized
variants are allowed only within the same engineering effect.

- MS-06 declares a selector; MA-28/29/30 apply it to current objects.
- MS-07 plans refresh; MA-31 performs refresh; ER-05 repairs a missing refresh.
- EX-03 maximizes the window; VI-01 observes viewport readiness.
- EX-14 saves; VA-20 checks that save; VA-22 reopens; VA-23 checks a property.
- ER-12 dispatches one retry after clean-entry preparation. Preparation, loading,
  and waiting remain separate; EX-09 may supply the dispatch mechanism.
- VA-25 retains the approved label but checks one property on already reimported
  geometry. MA-35 supplies the import; the combined reimport-and-check procedure
  belongs to the case.
- ER-07/09/10 require one diagnosed defect or state and one selected repair per
  invocation; they do not promise a universal repair implementation.
- Coordinate-frame fields form one coherent frame; source-view mapping is GU-16.

## Case decomposition acceptance

For a new source, record its requirements, assign operation instances to catalog
IDs, and put instance parameters and order in the case. For each instance record
the input provider, expected effect, available template scope, and missing
evidence. Check every requested feature and deliverable for coverage. Mark a gap
when no action fits rather than stretching an unrelated template. A drawing's
ambiguity is an input issue; a missing implementation is a maturity gap; an
unrepresentable engineering effect is a catalog gap. These are separate results.

Catalog validation checks schema-like field constraints, ID coverage, stage
assignment, and registry correspondence. It cannot prove correct visual
interpretation or successful modeling.

Run `python -B spaceclaim-vision-modeling/scripts/validate_operation_catalog.py`
from the repository root after changing catalog definitions or their registry
mapping. This check is independent of the full test suite.
