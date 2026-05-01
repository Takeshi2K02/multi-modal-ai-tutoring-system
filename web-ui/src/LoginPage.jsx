import { useState, useEffect } from "react";
import { useAuth } from "./AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { 
  GraduationCap, ArrowRight, ArrowLeft, User, Lock, Mail, 
  Sparkles, Calendar, Briefcase, Brain, Target, ShieldCheck,
  CheckCircle2
} from "lucide-react";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [tab, setTab] = useState("login");
  const [step, setStep] = useState(1);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    birthday: "",
    role: "student",
    preferred_learning_style: "visual",
    interested_areas: [],
    strengths: [],
    weaknesses: []
  });

  const [tempTag, setTempTag] = useState("");

  const updateForm = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleSelection = (field, item) => {
    const current = formData[field];
    if (current.includes(item)) {
      updateForm(field, current.filter(i => i !== item));
    } else {
      updateForm(field, [...current, item]);
    }
  };

  const handleNext = () => {
    if (step < 4) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  async function handleSubmit(e) {
    if (e) e.preventDefault();
    
    // STRICT STEP VALIDATION
    if (tab === "register" && step < 4) {
      // If they somehow trigger a submit (e.g. Enter key), just go to next step
      handleNext();
      return;
    }

    if (loading) return;
    setError(null);
    setLoading(true);

    try {
      if (tab === "login") {
        await login(formData.email, formData.password);
      } else {
        // Final Registration
        const payload = {
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password, // Send plain, backend will hash
          birthday: formData.birthday,
          role: formData.role,
          preferred_learning_style: formData.preferred_learning_style,
          interested_areas: formData.interested_areas,
          strengths: formData.strengths,
          weaknesses: formData.weaknesses
        };
        await register(payload);
        
        // Success State
        setTab("login");
        setStep(1);
        setError("Account created successfully! Please sign in.");
        // Clear sensitive form data
        updateForm("password", "");
      }
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const PRESET_STRENGTHS = ["Critical Thinking", "Problem Solving", "Memory", "Creativity", "Technical Skills", "Communication"];
  const PRESET_WEAKNESSES = ["Time Management", "Focus", "Public Speaking", "Procrastination", "Abstract Concepts", "Math"];

  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Full Name</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                  <User size={18} />
                </div>
                <input
                  type="text"
                  placeholder="John Doe"
                  value={formData.full_name}
                  onChange={(e) => updateForm("full_name", e.target.value)}
                  className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Email Address</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                  <Mail size={18} />
                </div>
                <input
                  type="email"
                  placeholder="john@example.com"
                  value={formData.email}
                  onChange={(e) => updateForm("email", e.target.value)}
                  className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Password</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                  <Lock size={18} />
                </div>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => updateForm("password", e.target.value)}
                  className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                  required
                />
              </div>
            </div>
          </motion.div>
        );
      case 2:
        return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Birthday</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                  <Calendar size={18} />
                </div>
                <input
                  type="date"
                  value={formData.birthday}
                  onChange={(e) => updateForm("birthday", e.target.value)}
                  className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all color-scheme-dark"
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Role</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                  <Briefcase size={18} />
                </div>
                <select
                  value={formData.role}
                  onChange={(e) => updateForm("role", e.target.value)}
                  className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all appearance-none"
                >
                  <option value="student">Student</option>
                  <option value="instructor">Instructor</option>
                </select>
              </div>
            </div>
          </motion.div>
        );
      case 3:
        return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Preferred Learning Style</label>
              <div className="grid grid-cols-3 gap-2">
                {["textual", "visual", "auditory"].map(style => (
                  <button
                    key={style}
                    type="button"
                    onClick={() => updateForm("preferred_learning_style", style)}
                    className={`py-2 px-1 rounded-xl border text-xs capitalize transition-all ${
                      formData.preferred_learning_style === style 
                        ? "bg-primary/20 border-primary text-white" 
                        : "bg-black/20 border-white/5 text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Interested Areas</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.interested_areas.map(area => (
                  <span key={area} className="bg-primary/10 text-primary text-[10px] px-2 py-1 rounded-full flex items-center gap-1 border border-primary/20">
                    {area}
                    <button type="button" onClick={() => toggleSelection("interested_areas", area)}>×</button>
                  </span>
                ))}
              </div>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Type and press Enter (e.g. AI, Math)"
                  value={tempTag}
                  onChange={(e) => setTempTag(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && tempTag.trim()) {
                      e.preventDefault();
                      if (!formData.interested_areas.includes(tempTag.trim())) {
                        toggleSelection("interested_areas", tempTag.trim());
                      }
                      setTempTag("");
                    }
                  }}
                  className="w-full bg-black/30 border border-white/10 rounded-2xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                />
              </div>
            </div>
          </motion.div>
        );
      case 4:
        return (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Strengths</label>
              <div className="grid grid-cols-2 gap-2">
                {PRESET_STRENGTHS.map(item => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleSelection("strengths", item)}
                    className={`text-left px-3 py-2 rounded-xl border text-[11px] transition-all flex items-center justify-between ${
                      formData.strengths.includes(item)
                        ? "bg-secondary/20 border-secondary text-white"
                        : "bg-black/20 border-white/5 text-zinc-500"
                    }`}
                  >
                    {item}
                    {formData.strengths.includes(item) && <CheckCircle2 size={14} className="text-secondary" />}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Weaknesses</label>
              <div className="grid grid-cols-2 gap-2">
                {PRESET_WEAKNESSES.map(item => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleSelection("weaknesses", item)}
                    className={`text-left px-3 py-2 rounded-xl border text-[11px] transition-all flex items-center justify-between ${
                      formData.weaknesses.includes(item)
                        ? "bg-danger/20 border-danger text-white"
                        : "bg-black/20 border-white/5 text-zinc-500"
                    }`}
                  >
                    {item}
                    {formData.weaknesses.includes(item) && <CheckCircle2 size={14} className="text-danger" />}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        );
      default: return null;
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-edu-bg-dark mesh-gradient relative overflow-hidden p-6">
      {/* Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/10 rounded-full blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg z-10"
      >
        <div className="glass-panel p-8 rounded-[32px] border-white/5 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-accent to-secondary" />

          <div className="flex flex-col items-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center mb-3">
              <GraduationCap className="text-white" size={28} />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              EduSynth <span className="text-accent font-light">AI</span>
            </h1>
            {tab === "register" && (
              <div className="flex gap-2 mt-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${step === i ? "w-8 bg-primary" : "w-4 bg-white/10"}`} />
                ))}
              </div>
            )}
          </div>

          <div className="flex bg-black/20 p-1 rounded-xl mb-6 border border-white/5">
            <button
              onClick={() => { setTab("login"); setStep(1); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                tab === "login" ? "bg-primary text-white shadow-lg" : "text-zinc-400 hover:text-white"
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setTab("register")}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                tab === "register" ? "bg-primary text-white shadow-lg" : "text-zinc-400 hover:text-white"
              }`}
            >
              Register
            </button>
          </div>

          <form 
            className="space-y-6"
            onKeyDown={(e) => {
              if (e.key === "Enter" && tab === "register") {
                if (step < 4) {
                  e.preventDefault();
                  handleNext();
                }
              }
            }}
          >
            {tab === "login" ? (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Email Address</label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                      <Mail size={18} />
                    </div>
                    <input
                      type="email"
                      placeholder="john@example.com"
                      value={formData.email}
                      onChange={(e) => updateForm("email", e.target.value)}
                      className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider ml-1">Password</label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-500 group-focus-within:text-primary transition-colors">
                      <Lock size={18} />
                    </div>
                    <input
                      type="password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => updateForm("password", e.target.value)}
                      className="w-full bg-black/30 border border-white/10 rounded-2xl pl-11 pr-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                      required
                    />
                  </div>
                </div>
              </div>
            ) : renderStep()}

            {error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-danger/10 border border-danger/20 rounded-xl p-3 text-center">
                <p className="text-danger text-xs font-medium">{error}</p>
              </motion.div>
            )}

            <div className="flex gap-3">
              {tab === "register" && step > 1 && (
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 bg-white/5 hover:bg-white/10 text-white font-bold py-4 rounded-2xl transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft size={18} />
                  Back
                </button>
              )}
              
              {tab === "register" && step < 4 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="flex-1 bg-primary hover:bg-primary/90 text-white font-bold py-4 rounded-2xl shadow-xl shadow-primary/20 transition-all flex items-center justify-center gap-2"
                >
                  Continue
                  <ArrowRight size={18} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-[2] group relative flex items-center justify-center bg-primary hover:bg-primary/90 text-white font-bold py-4 rounded-2xl shadow-xl shadow-primary/20 transition-all disabled:opacity-50"
                >
                  {loading ? <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : (
                    <>
                      <span>{tab === "login" ? "Sign In" : "Complete Registration"}</span>
                      <ShieldCheck size={20} className="ml-2" />
                    </>
                  )}
                </button>
              )}
            </div>
          </form>
        </div>
        
        <div className="mt-6 flex items-center justify-center gap-2 text-zinc-500 text-xs">
          <Sparkles size={14} className="text-accent" />
          <span>Advanced AI-Personalized Learning Core</span>
        </div>
      </motion.div>
    </div>
  );
}


