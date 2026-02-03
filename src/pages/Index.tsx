import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

const Index = () => {
  const [balance, setBalance] = useState(100);
  const [betAmount, setBetAmount] = useState(10);
  const [selectedSide, setSelectedSide] = useState<'heads' | 'tails' | null>(null);
  const [isFlipping, setIsFlipping] = useState(false);
  const [lastResult, setLastResult] = useState<'heads' | 'tails' | null>(null);
  
  const [totalGames, setTotalGames] = useState(0);
  const [wins, setWins] = useState(0);
  const [totalWinnings, setTotalWinnings] = useState(0);

  const handleFlip = () => {
    if (!selectedSide) {
      toast.error('Выберите сторону монеты');
      return;
    }
    
    if (betAmount > balance) {
      toast.error('Недостаточно средств');
      return;
    }

    if (betAmount <= 0) {
      toast.error('Укажите сумму ставки');
      return;
    }

    setIsFlipping(true);
    
    setTimeout(() => {
      const result = Math.random() > 0.5 ? 'heads' : 'tails';
      setLastResult(result);
      setIsFlipping(false);
      
      setTotalGames(prev => prev + 1);
      
      if (result === selectedSide) {
        const winAmount = betAmount * 2;
        setBalance(prev => prev + betAmount);
        setWins(prev => prev + 1);
        setTotalWinnings(prev => prev + winAmount);
        toast.success(`Вы выиграли ${winAmount} TON!`);
      } else {
        setBalance(prev => prev - betAmount);
        toast.error(`Вы проиграли ${betAmount} TON`);
      }
      
      setSelectedSide(null);
    }, 2000);
  };

  const winRate = totalGames > 0 ? ((wins / totalGames) * 100).toFixed(1) : '0.0';

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">CoinFlip</h1>
          <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-lg border border-border">
            <Icon name="Wallet" size={20} className="text-primary" />
            <span className="font-semibold">{balance.toFixed(2)} TON</span>
          </div>
        </div>

        <Tabs defaultValue="game" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="game" className="flex items-center gap-2">
              <Icon name="Coins" size={18} />
              <span>Игра</span>
            </TabsTrigger>
            <TabsTrigger value="wallet" className="flex items-center gap-2">
              <Icon name="Wallet" size={18} />
              <span>Кошелёк</span>
            </TabsTrigger>
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <Icon name="User" size={18} />
              <span>Профиль</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="game" className="space-y-6">
            <Card className="p-8 md:p-12 bg-card border-border">
              <div className="flex flex-col items-center space-y-8">
                <div 
                  className={`w-32 h-32 md:w-40 md:h-40 rounded-full flex items-center justify-center text-6xl md:text-7xl font-bold shadow-2xl transition-all ${
                    isFlipping ? 'animate-flip' : ''
                  } ${
                    lastResult === 'heads' ? 'bg-primary text-primary-foreground' : 
                    lastResult === 'tails' ? 'bg-secondary text-secondary-foreground' : 
                    'bg-muted text-muted-foreground'
                  }`}
                >
                  {isFlipping ? '?' : lastResult === 'heads' ? '🪙' : lastResult === 'tails' ? '💎' : '?'}
                </div>

                {!isFlipping && lastResult && (
                  <div className="text-center animate-fade-in">
                    <p className="text-lg text-muted-foreground">Результат:</p>
                    <p className="text-2xl font-bold">
                      {lastResult === 'heads' ? 'Орёл 🪙' : 'Решка 💎'}
                    </p>
                  </div>
                )}

                <div className="w-full max-w-md space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground mb-2 block">Сумма ставки</label>
                    <Input
                      type="number"
                      value={betAmount}
                      onChange={(e) => setBetAmount(Number(e.target.value))}
                      className="text-lg"
                      disabled={isFlipping}
                      min={1}
                    />
                  </div>

                  <div className="flex gap-3">
                    {[5, 10, 25, 50].map((amount) => (
                      <Button
                        key={amount}
                        variant="outline"
                        size="sm"
                        onClick={() => setBetAmount(amount)}
                        disabled={isFlipping}
                        className="flex-1"
                      >
                        {amount}
                      </Button>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-4">
                    <Button
                      size="lg"
                      variant={selectedSide === 'heads' ? 'default' : 'outline'}
                      onClick={() => setSelectedSide('heads')}
                      disabled={isFlipping}
                      className="text-lg py-8"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-3xl">🪙</span>
                        <span>Орёл</span>
                      </div>
                    </Button>
                    <Button
                      size="lg"
                      variant={selectedSide === 'tails' ? 'default' : 'outline'}
                      onClick={() => setSelectedSide('tails')}
                      disabled={isFlipping}
                      className="text-lg py-8"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-3xl">💎</span>
                        <span>Решка</span>
                      </div>
                    </Button>
                  </div>

                  <Button
                    size="lg"
                    className="w-full text-lg py-6"
                    onClick={handleFlip}
                    disabled={isFlipping || !selectedSide}
                  >
                    {isFlipping ? (
                      <span className="flex items-center gap-2">
                        <Icon name="Loader2" className="animate-spin" size={20} />
                        Бросаем...
                      </span>
                    ) : (
                      'Бросить монету'
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="wallet" className="space-y-6">
            <Card className="p-6 bg-card border-border">
              <div className="space-y-6">
                <div className="text-center py-6">
                  <p className="text-sm text-muted-foreground mb-2">Текущий баланс</p>
                  <p className="text-4xl font-bold">{balance.toFixed(2)} TON</p>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <Card className="p-6 bg-muted border-border">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Icon name="ArrowDownToLine" size={20} className="text-primary" />
                      Пополнить
                    </h3>
                    <div className="space-y-4">
                      <Input
                        placeholder="Сумма пополнения"
                        type="number"
                      />
                      <Input
                        placeholder="Memo (опционально)"
                      />
                      <Button className="w-full">
                        <Icon name="Plus" size={18} className="mr-2" />
                        Создать запрос
                      </Button>
                    </div>
                  </Card>

                  <Card className="p-6 bg-muted border-border">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Icon name="ArrowUpFromLine" size={20} className="text-secondary" />
                      Вывести
                    </h3>
                    <div className="space-y-4">
                      <Input
                        placeholder="Сумма вывода"
                        type="number"
                      />
                      <Input
                        placeholder="TON адрес"
                      />
                      <Button className="w-full" variant="secondary">
                        <Icon name="Send" size={18} className="mr-2" />
                        Отправить запрос
                      </Button>
                    </div>
                  </Card>
                </div>

                <Card className="p-6 bg-muted border-border">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Icon name="History" size={20} className="text-primary" />
                    История транзакций
                  </h3>
                  <div className="text-center py-8 text-muted-foreground">
                    <Icon name="FileText" size={48} className="mx-auto mb-3 opacity-50" />
                    <p>Транзакции пока отсутствуют</p>
                  </div>
                </Card>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="profile" className="space-y-6">
            <Card className="p-6 bg-card border-border">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center text-2xl">
                  🎮
                </div>
                <div>
                  <h2 className="text-2xl font-bold">Игрок #12345</h2>
                  <p className="text-muted-foreground">Участник с сегодня</p>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <Card className="p-6 bg-muted border-border text-center">
                  <Icon name="Target" size={32} className="mx-auto mb-3 text-primary" />
                  <p className="text-sm text-muted-foreground mb-1">Процент побед</p>
                  <p className="text-3xl font-bold">{winRate}%</p>
                </Card>

                <Card className="p-6 bg-muted border-border text-center">
                  <Icon name="TrendingUp" size={32} className="mx-auto mb-3 text-secondary" />
                  <p className="text-sm text-muted-foreground mb-1">Общий выигрыш</p>
                  <p className="text-3xl font-bold">{totalWinnings.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground mt-1">TON</p>
                </Card>

                <Card className="p-6 bg-muted border-border text-center">
                  <Icon name="GamepadIcon" size={32} className="mx-auto mb-3 text-accent" />
                  <p className="text-sm text-muted-foreground mb-1">Всего игр</p>
                  <p className="text-3xl font-bold">{totalGames}</p>
                </Card>
              </div>

              <Card className="p-6 bg-muted border-border mt-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Icon name="BarChart3" size={20} className="text-primary" />
                  Статистика
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Побед:</span>
                    <span className="font-semibold">{wins}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Поражений:</span>
                    <span className="font-semibold">{totalGames - wins}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Средняя ставка:</span>
                    <span className="font-semibold">{totalGames > 0 ? (totalWinnings / totalGames / 2).toFixed(2) : '0.00'} TON</span>
                  </div>
                </div>
              </Card>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
