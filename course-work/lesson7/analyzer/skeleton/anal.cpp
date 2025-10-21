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

    struct SkeletonPass : public PassInfoMixin<SkeletonPass>
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
                    errs() << "  Found a loop with " << L->getNumBlocks() << " blocks.\n";

                    BasicBlock *header = L->getHeader();
                    BasicBlock *latch = L->getLoopLatch();
                    Instruction *headerTerm = header->getTerminator();
                    Instruction *latchTerm = latch->getTerminator();
                    int64_t bound;
                    Value *potentialIter, *latchCond;
                    bool resolvable = false;
                    if (auto *brInst = dyn_cast<BranchInst>(headerTerm))
                    {
                        if (brInst->isConditional())
                        {
                            Value *Cond = brInst->getCondition();
                            errs() << "  Branch condition: " << *Cond << "\n";

                            if (auto *Cmp = dyn_cast<ICmpInst>(Cond))
                            {
                                latchCond = Cmp;
                                errs() << "  Comparison predicate: " << Cmp->getPredicate() << "\n";
                                Value *Op0 = Cmp->getOperand(0);
                                Value *Op1 = Cmp->getOperand(1);

                                if (auto *CI = dyn_cast<ConstantInt>(Op0))
                                {
                                    bound = CI->getSExtValue();
                                    if (auto *LI = dyn_cast<LoadInst>(Op1))
                                    {
                                        potentialIter = LI->getPointerOperand();
                                        resolvable = true;
                                    }
                                }
                                if (auto *CI = dyn_cast<ConstantInt>(Op1))
                                {
                                    bound = CI->getSExtValue();
                                    if (auto *LI = dyn_cast<LoadInst>(Op0))
                                    {
                                        potentialIter = LI->getPointerOperand();
                                        resolvable = true;
                                    }
                                }
                            }
                        }
                    }
                    if (resolvable)
                    {
                        int64_t inc;
                        bool updated = false;
                        for (BasicBlock *BB : L->blocks())
                        {
                            for (Instruction &I : *BB)
                            {
                                if (auto *Store = dyn_cast<StoreInst>(&I))
                                    if (Store->getPointerOperand() == potentialIter)
                                    {
                                        const SCEV *S = SE.getSCEV(Store->getValueOperand());
                                        if (auto *Add = dyn_cast<SCEVAddExpr>(S))
                                        {
                                            if (Add->getNumOperands() != 2)
                                            {
                                                resolvable = false;
                                            }
                                            else
                                            {
                                                bool foundInc = false;
                                                for (const auto *Op : Add->operands())
                                                {
                                                    if (auto *CI = dyn_cast<SCEVConstant>(Op))
                                                    {
                                                        inc = CI->getValue()->getSExtValue();
                                                        foundInc = true;
                                                    }
                                                    else if (auto *SU = dyn_cast<SCEVUnknown>(Op))
                                                    {
                                                        Value *V = SU->getValue();
                                                        if (auto *LI = dyn_cast<LoadInst>(V))
                                                        {
                                                            if (LI->getPointerOperand() != potentialIter)
                                                            {
                                                                resolvable = false;
                                                                break;
                                                            }
                                                        }
                                                        else
                                                        {
                                                            resolvable = false;
                                                            break;
                                                        }
                                                    }
                                                    else
                                                    {
                                                        resolvable = false;
                                                        break;
                                                    }
                                                }
                                                if (!foundInc || updated)
                                                {
                                                    resolvable = false;
                                                }
                                                else
                                                {
                                                    updated = true;
                                                }
                                            }
                                        }
                                    }
                            }
                        }
                        if (resolvable)
                        {
                            errs() << "=====================\n";
                            errs() << "Found loop iterator " << *potentialIter << "\n\tincrease by " << inc << " bounded to " << bound << ".\nThe condition is:\t" << *latchCond <<  "\n";
                            errs() << "=====================\n";
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
        .PluginName = "Skeleton pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB)
        {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level)
                {
                    MPM.addPass(SkeletonPass());
                });
        }};
}
