#include "llvm/Pass.h"
#include "llvm/IR/Module.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Analysis/LoopAnalysisManager.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionExpressions.h"

using namespace llvm;

namespace
{
    struct LoopIterAnalyzePass : public PassInfoMixin<LoopIterAnalyzePass>
    {
        PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM)
        {
            auto &FAM = AM.getResult<FunctionAnalysisManagerModuleProxy>(M).getManager();
            for (Function &F : M)
            {
                if (F.isDeclaration())
                {
                    continue;
                }
                // function name
                errs() << "Function: " << F.getName() << "\n";
                auto &LI = FAM.getResult<LoopAnalysis>(F);
                auto &SE = FAM.getResult<ScalarEvolutionAnalysis>(F);
                for (Loop *L : LI)
                {
                    // errs() << "  Found a loop with " << L->getNumBlocks() << " blocks.\n";
                    BasicBlock *header = L->getHeader();
                    BasicBlock *latch = L->getLoopLatch();
                    Value *bound = nullptr;
                    Value *recIter = nullptr;
                    ICmpInst *cmp = nullptr;
                    if (cmp = L->getLatchCmpInst())
                    {
                        if (L->isLoopInvariant(cmp->getOperand(0)))
                        {
                            bound = cmp->getOperand(0);
                            const SCEV *S = SE.getSCEV(cmp->getOperand(1));
                            if (const SCEVAddRecExpr *AddRec = dyn_cast<SCEVAddRecExpr>(S))
                            {
                                if (AddRec->getLoop() == L)
                                {
                                    recIter = cmp->getOperand(1);
                                }
                            }
                        }
                        if (L->isLoopInvariant(cmp->getOperand(1)))
                        {
                            bound = cmp->getOperand(1);
                            const SCEV *S = SE.getSCEV(cmp->getOperand(0));
                            if (const SCEVAddRecExpr *AddRec = dyn_cast<SCEVAddRecExpr>(S))
                            {
                                if (AddRec->getLoop() == L)
                                {
                                    recIter = cmp->getOperand(0);
                                }
                            }
                        }
                    }
                    if (bound != nullptr && recIter != nullptr)
                    {
                        Value *iter = nullptr;
                        for (auto &I : *header)
                        {
                            if (auto *PHI = dyn_cast<PHINode>(&I))
                            {
                                for (unsigned idx = 0; idx < PHI->getNumIncomingValues(); ++idx)
                                {
                                    Value *incoming = PHI->getIncomingValue(idx);
                                    if (incoming == recIter)
                                    {
                                        iter = PHI;
                                    }
                                }
                            }
                        }
                        if (iter != nullptr)
                        {
                            const SCEV *S = SE.getSCEV(iter);
                            llvm::outs() << "===================================\n";
                            llvm::outs() << "Loop: " << L->getName() << "\n";
                            llvm::outs() << "-----------------------------------\n";
                            llvm::outs() << "Iter: " << *iter << "\t(" << *S << ")\n";
                            llvm::outs() << "Bound: " << *bound << "\n";
                            llvm::outs() << "Cmp Predicate: " << cmp->getPredicate() << "\n";
                            llvm::outs() << "===================================\n\n";
                        }
                    }
                }
            }
            return PreservedAnalyses::all();
        };
    };
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo()
{
    return {
        .APIVersion = LLVM_PLUGIN_API_VERSION,
        .PluginName = "LoopIterAnalyze pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB)
        {
            PB.registerOptimizerLastEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level)
                {
                    MPM.addPass(LoopIterAnalyzePass());
                });
        }};
}
